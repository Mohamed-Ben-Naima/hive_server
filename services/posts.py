# hive_server/services/posts.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, select, literal_column
from fastapi import HTTPException, status, UploadFile
import logging
from typing import List, Optional

from ..utils import file_manager

logger = logging.getLogger("tea_n_hive_logger.posts_service")

from ..models import posts as posts_model
from ..models import user as user_model
from ..models import post_likes as post_likes_model
from ..models import post_comments as post_comments_model # <--- NEW: Import post_comments model
from ..schemas import posts as posts_schema

class PostsService:
    def __init__(self, db: Session):
        self.db = db

    async def create_post(self, user_id: int, post_data: posts_schema.PostCreate, media_file: Optional[UploadFile]) -> posts_model.Post:
        """
        Creates a new post for a given user, handling optional file uploads and flexible content validation.
        Ensures the user exists and returns the newly created post with its author's profile eager-loaded.
        """
        logger.info(f"Attempting to create a new post for user ID: {user_id}.")
        
        user_exists = self.db.query(user_model.User).filter(user_model.User.user_id == user_id).first()
        if not user_exists:
            logger.warning(f"Post creation failed: User ID {user_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )

        media_filename_to_save = None
        
        has_text_content = bool(post_data.text_content and post_data.text_content.strip())
        has_media_file_provided = media_file is not None

        if post_data.post_type == "TEXT":
            if not has_text_content:
                logger.warning("Post creation failed: TEXT post type requires text_content.")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="TEXT post type requires text content."
                )
            if has_media_file_provided:
                logger.warning("Post creation failed: TEXT post type does not allow media file uploads.")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="TEXT post type does not allow media file uploads."
                )
        elif post_data.post_type in ["IMAGE", "VIDEO"]:
            if not has_text_content and not has_media_file_provided:
                logger.warning(f"Post creation failed: {post_data.post_type} post type requires either text_content or a media file.")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{post_data.post_type} post type requires either text content or a media file."
                )
            if has_media_file_provided:
                media_filename_to_save = await file_manager.save_upload_file(media_file)

        try:
            db_post = posts_model.Post(
                user_id=user_id,
                post_type=post_data.post_type,
                text_content=post_data.text_content,
                media_url=media_filename_to_save
            )
            self.db.add(db_post)
            self.db.commit()
            self.db.refresh(db_post)

            # Re-fetch the post with all necessary relationships eager-loaded for Pydantic.
            # Pass current_user_id=None because this is a creation, not a retrieval for a specific user.
            final_db_post = self.get_post_by_id(db_post.post_id, current_user_id=None)
            if not final_db_post:
                logger.error(f"Failed to retrieve newly created post ID: {db_post.post_id} after creation.")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve newly created post for response."
                )

            logger.info(f"Successfully created post ID: {final_db_post.post_id} for user ID: {user_id}.")
            return final_db_post
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Failed to create post for user ID: {user_id}. Rolling back transaction.")
            if media_filename_to_save:
                file_manager.delete_file(media_filename_to_save)
                logger.info(f"Cleaned up orphaned file: {media_filename_to_save}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create post due to a server error: {e}"
            )

    def get_post_by_id(self, post_id: int, current_user_id: Optional[int] = None) -> Optional[posts_model.Post]:
        """
        Retrieves a single post by its ID, with its author's user and profile eager-loaded,
        and includes likes count, current user's like status, and comments count.
        """
        logger.debug(f"Attempting to retrieve post by ID: {post_id}.")

        # Subquery to count likes for the post
        likes_count_subquery = select(func.count(post_likes_model.PostLike.like_id))\
            .where(post_likes_model.PostLike.post_id == posts_model.Post.post_id)\
            .scalar_subquery()

        # Subquery to check if current user liked the post
        is_liked_subquery = select(
            func.count(post_likes_model.PostLike.like_id)
        ).where(
            post_likes_model.PostLike.post_id == posts_model.Post.post_id,
            post_likes_model.PostLike.user_id == current_user_id # Filter by current user ID
        ).scalar_subquery()

        # --- NEW: Subquery to count comments for the post ---
        comments_count_subquery = select(func.count(post_comments_model.PostComment.comment_id))\
            .where(post_comments_model.PostComment.post_id == posts_model.Post.post_id)\
            .scalar_subquery()
        # --- END NEW ---

        # Build the main query for the post
        stmt = select(
            posts_model.Post,
            likes_count_subquery.label("likes_count"),
            is_liked_subquery.label("is_liked_by_current_user"),
            comments_count_subquery.label("comments_count") # <--- NEW: Add comments count to select
        ).options(
            joinedload(posts_model.Post.user).joinedload(user_model.User.profile)
        ).filter(posts_model.Post.post_id == post_id)

        # Execute the query
        result = self.db.execute(stmt).first()

        if not result:
            logger.warning(f"Post ID: {post_id} not found.")
            return None
        
        # Unpack the result: Post object and the three scalar values
        post_orm_obj, likes_count, is_liked_by_current_user_int, comments_count = result # <--- MODIFIED: Unpack comments_count

        # Manually attach the calculated values to the ORM object for Pydantic serialization
        post_orm_obj.likes_count = likes_count
        post_orm_obj.is_liked_by_current_user = bool(is_liked_by_current_user_int)
        post_orm_obj.comments_count = comments_count # <--- NEW: Attach comments_count

        logger.debug(f"Successfully retrieved post ID: {post_id} with likes count: {likes_count}, is_liked: {bool(is_liked_by_current_user_int)}, comments count: {comments_count}.") # <--- MODIFIED: Log comments_count
        return post_orm_obj

    def get_posts(self, skip: int = 0, limit: int = 10, current_user_id: Optional[int] = None) -> List[posts_model.Post]:
        """
        Retrieves a paginated list of posts, with each post's author and profile eager-loaded,
        and includes likes count, current user's like status, and comments count.
        """
        logger.debug(f"Attempting to retrieve posts (skip: {skip}, limit: {limit}).")

        # Define aliases for tables to make joins clearer
        Post = posts_model.Post
        User = user_model.User
        PostLike = post_likes_model.PostLike
        PostComment = post_comments_model.PostComment # <--- NEW: Alias for PostComment

        # Subquery for likes count
        likes_count_cte = select(
            PostLike.post_id,
            func.count(PostLike.like_id).label("likes_count")
        ).group_by(PostLike.post_id).cte("likes_count_cte")

        # Subquery for current user's like status
        is_liked_cte = select(
            PostLike.post_id
        ).where(
            PostLike.user_id == current_user_id
        ).cte("is_liked_cte")

        # --- NEW: Subquery for comments count ---
        comments_count_cte = select(
            PostComment.post_id,
            func.count(PostComment.comment_id).label("comments_count")
        ).group_by(PostComment.post_id).cte("comments_count_cte")
        # --- END NEW ---

        # Build the main query
        stmt = select(
            Post,
            func.coalesce(likes_count_cte.c.likes_count, 0).label("likes_count"),
            (is_liked_cte.c.post_id.is_not(None)).label("is_liked_by_current_user"),
            func.coalesce(comments_count_cte.c.comments_count, 0).label("comments_count") # <--- NEW: Add comments count to select
        ).options(
            joinedload(Post.user).joinedload(User.profile)
        ).outerjoin(
            likes_count_cte, Post.post_id == likes_count_cte.c.post_id
        ).outerjoin(
            is_liked_cte, Post.post_id == is_liked_cte.c.post_id
        ).outerjoin( # <--- NEW: Outer join for comments count
            comments_count_cte, Post.post_id == comments_count_cte.c.post_id
        ).order_by(
            Post.created_at.desc()
        ).offset(skip).limit(limit)

        # Execute the query
        results = self.db.execute(stmt).all()

        posts_with_data = []
        for row in results:
            # Unpack the result: Post object, likes_count, is_liked_by_current_user, comments_count
            post_orm_obj, likes_count, is_liked_by_current_user_bool, comments_count = row # <--- MODIFIED: Unpack comments_count
            
            # Manually attach the calculated values to the ORM object
            post_orm_obj.likes_count = likes_count
            post_orm_obj.is_liked_by_current_user = is_liked_by_current_user_bool
            post_orm_obj.comments_count = comments_count # <--- NEW: Attach comments_count
            posts_with_data.append(post_orm_obj)

        logger.debug(f"Successfully retrieved {len(posts_with_data)} posts with likes and comments data.") # <--- MODIFIED: Log comments data
        return posts_with_data

    async def update_post(self, post_id: int, user_id: int, post_data: posts_schema.PostUpdate, media_file: Optional[UploadFile]) -> posts_model.Post:
        """
        Updates an existing post, handling optional file uploads and flexible content validation.
        Ensures the authenticated user is the owner.
        """
        logger.info(f"Attempting to update post ID: {post_id} by user ID: {user_id}.")
        db_post = self.db.query(posts_model.Post)\
            .options(joinedload(posts_model.Post.user).joinedload(user_model.User.profile))\
            .filter(posts_model.Post.post_id == post_id)\
            .first()

        if not db_post:
            logger.warning(f"Post update failed: Post ID {post_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found."
            )
        
        if db_post.user_id != user_id:
            logger.warning(f"Post update failed: User ID {user_id} is not the owner of post ID {post_id}.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this post."
            )

        old_media_filename = db_post.media_url
        new_media_filename = None

        if post_data.post_type is not None:
            db_post.post_type = post_data.post_type
        if post_data.text_content is not None:
            db_post.text_content = post_data.text_content

        if media_file:
            new_media_filename = await file_manager.save_upload_file(media_file)
            if old_media_filename:
                file_manager.delete_file(old_media_filename)
            db_post.media_url = new_media_filename
        elif post_data.post_type == "TEXT" and old_media_filename:
            file_manager.delete_file(old_media_filename)
            db_post.media_url = None
            logger.info(f"Removed media file {old_media_filename} for post {post_id} as post type changed to TEXT.")
        elif post_data.text_content is not None and not post_data.text_content.strip() and old_media_filename:
            if db_post.post_type == "TEXT":
                file_manager.delete_file(old_media_filename)
                db_post.media_url = None
                logger.info(f"Removed media file {old_media_filename} for post {post_id} as text content was cleared for TEXT post.")

        current_has_text_content = bool(db_post.text_content and db_post.text_content.strip())
        current_has_media = bool(db_post.media_url)

        if db_post.post_type == "TEXT":
            if not current_has_text_content:
                logger.warning("Post update failed: TEXT post type requires text_content after update.")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="TEXT post type requires text content."
                )
            if current_has_media:
                logger.warning("Post update failed: TEXT post type does not allow media file after update.")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="TEXT post type does not allow media file."
                )
        elif db_post.post_type in ["IMAGE", "VIDEO"]:
            if not current_has_text_content and not current_has_media:
                logger.warning(f"Post update failed: {db_post.post_type} post type requires either text_content or a media file after update.")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{db_post.post_type} post type requires either text content or a media file."
                )

        try:
            self.db.add(db_post)
            self.db.commit()
            self.db.refresh(db_post)
            
            # Re-fetch the post with all necessary relationships eager-loaded for Pydantic response.
            # Pass current_user_id for correct likes count and status.
            final_db_post = self.get_post_by_id(db_post.post_id, current_user_id=user_id)
            if not final_db_post:
                logger.error(f"Failed to retrieve updated post ID: {db_post.post_id} after update.")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve updated post for response."
                )

            logger.info(f"Successfully updated post ID: {post_id}.")
            return final_db_post
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.exception(f"An unexpected error occurred while updating post ID: {post_id} for user ID: {user_id}.")
            if media_file and new_media_filename:
                file_manager.delete_file(new_media_filename)
                logger.info(f"Cleaned up orphaned new file: {new_media_filename}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update post due to a server error: {e}"
            )

    def delete_post(self, post_id: int, user_id: int) -> None:
        """
        Deletes a post. Ensures the authenticated user is the owner and deletes associated media file.
        """
        logger.info(f"Attempting to delete post ID: {post_id} by user ID: {user_id}.")
        db_post = self.db.query(posts_model.Post).filter(posts_model.Post.post_id == post_id).first()

        if not db_post:
            logger.warning(f"Post deletion failed: Post ID {post_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found."
            )
        
        if db_post.user_id != user_id:
            logger.warning(f"Post deletion failed: User ID {user_id} is not the owner of post ID {post_id}.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this post."
            )

        try:
            if db_post.media_url:
                file_manager.delete_file(db_post.media_url)

            self.db.delete(db_post)
            self.db.commit()
            logger.info(f"Successfully deleted post ID: {post_id}.")
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Failed to delete post ID: {post_id}. Rolling back transaction.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete post due to a server error: {e}"
            )
