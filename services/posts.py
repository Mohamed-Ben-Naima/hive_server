# hive_server/services/posts.py

from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status, UploadFile
from typing import List, Optional
import logging

from ..utils import file_manager # Import the centralized file_manager utility

logger = logging.getLogger("tea_n_hive_logger.posts_service")

from ..models import posts as posts_model
from ..models import user as user_model
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
        
        # Verify user existence first.
        user_exists = self.db.query(user_model.User).filter(user_model.User.user_id == user_id).first()
        if not user_exists:
            logger.warning(f"Post creation failed: User ID {user_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )

        media_filename_to_save = None
        
        # --- Flexible Content Validation Logic (Create) ---
        # Rule: A post must have AT LEAST text_content OR a media_file.
        # Rule: TEXT posts must have text_content and NO media_file.
        # Rule: IMAGE/VIDEO posts can have both, or just one of them.

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
            # If media_file is provided and allowed by type, save it.
            if has_media_file_provided:
                media_filename_to_save = await file_manager.save_upload_file(media_file)
        # --- END Flexible Content Validation ---

        try:
            db_post = posts_model.Post(
                user_id=user_id,
                post_type=post_data.post_type,
                text_content=post_data.text_content,
                media_url=media_filename_to_save # Store only the filename
            )
            self.db.add(db_post)
            self.db.commit()
            self.db.refresh(db_post) # Refresh to get the post_id and created_at from DB

            # CRITICAL: Re-fetch the post with all necessary relationships eager-loaded for Pydantic.
            # This ensures that 'db_post.user.profile' is correctly loaded for serialization.
            final_db_post = self.get_post_by_id(db_post.post_id)
            if not final_db_post: # This case should ideally not be hit if creation was successful
                logger.error(f"Failed to retrieve newly created post ID: {db_post.post_id} after creation.")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve newly created post for response."
                )

            logger.info(f"Successfully created post ID: {final_db_post.post_id} for user ID: {user_id}.")
            return final_db_post
        except HTTPException: # Re-raise HTTP exceptions from validation or user not found
            raise
        except Exception as e:
            self.db.rollback() # Rollback DB transaction on error
            logger.exception(f"Failed to create post for user ID: {user_id}. Rolling back transaction.")
            # If a file was saved but DB transaction failed, delete the file to prevent orphans.
            if media_filename_to_save:
                file_manager.delete_file(media_filename_to_save)
                logger.info(f"Cleaned up orphaned file: {media_filename_to_save}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create post due to a server error: {e}"
            )

    def get_post_by_id(self, post_id: int) -> Optional[posts_model.Post]:
        """
        Retrieves a single post by its ID, with its author's user and profile eager-loaded.
        """
        logger.debug(f"Attempting to retrieve post by ID: {post_id}.")
        post = self.db.query(posts_model.Post)\
            .options(joinedload(posts_model.Post.user).joinedload(user_model.User.profile))\
            .filter(posts_model.Post.post_id == post_id)\
            .first()
        
        if not post:
            logger.warning(f"Post ID: {post_id} not found.")
            return None
        
        logger.debug(f"Successfully retrieved post ID: {post_id}.")
        return post

    def get_posts(self, skip: int = 0, limit: int = 10) -> List[posts_model.Post]:
        """
        Retrieves a paginated list of posts, with each post's author and profile eager-loaded.
        """
        logger.debug(f"Attempting to retrieve posts (skip: {skip}, limit: {limit}).")
        posts = self.db.query(posts_model.Post)\
            .options(joinedload(posts_model.Post.user).joinedload(user_model.User.profile))\
            .order_by(posts_model.Post.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
        
        logger.debug(f"Successfully retrieved {len(posts)} posts.")
        return posts
    
    async def update_post(self, post_id: int, user_id: int, post_data: posts_schema.PostUpdate, media_file: Optional[UploadFile]) -> posts_model.Post:
        """
        Updates an existing post, handling optional file uploads and flexible content validation.
        Ensures the authenticated user is the owner.
        """
        logger.info(f"Attempting to update post ID: {post_id} by user ID: {user_id}.")
        # Fetch the post with eager loading for current state and eventual response
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

        old_media_filename = db_post.media_url # Store current filename for potential deletion
        new_media_filename = None # To track new file if uploaded

        # Apply updates to db_post based on provided data from post_data schema
        # Only update fields if they are explicitly provided in the update request
        if post_data.post_type is not None:
            db_post.post_type = post_data.post_type
        if post_data.text_content is not None: # Allows clearing text_content by sending ""
            db_post.text_content = post_data.text_content

        # --- REFINED MEDIA HANDLING LOGIC (UPDATE) ---
        if media_file: # Case 1: A new media file is provided
            new_media_filename = await file_manager.save_upload_file(media_file)
            if old_media_filename: # Delete old file if it existed
                file_manager.delete_file(old_media_filename)
            db_post.media_url = new_media_filename
        elif post_data.post_type == "TEXT" and old_media_filename:
            # Case 2: Post type is explicitly changed to TEXT, and there was existing media.
            # This implies removal of media.
            file_manager.delete_file(old_media_filename)
            db_post.media_url = None
            logger.info(f"Removed media file {old_media_filename} for post {post_id} as post type changed to TEXT.")
        # Case 3: No new media_file, post_type not changed to TEXT.
        # The existing db_post.media_url remains as is.
        # This covers scenarios where text_content is updated for a media post,
        # or a text post's text_content is updated.
        # --- END REFINED MEDIA HANDLING LOGIC ---

        # --- Flexible Content Validation Logic (Update - on final state of db_post) ---
        # Re-validate the post's content state after applying all updates.
        current_has_text_content = bool(db_post.text_content and db_post.text_content.strip())
        current_has_media = bool(db_post.media_url)

        if db_post.post_type == "TEXT":
            if not current_has_text_content:
                logger.warning("Post update failed: TEXT post type requires text_content after update.")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="TEXT post type requires text content."
                )
            if current_has_media: # A TEXT post should not have media_url
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
        # --- END Flexible Content Validation ---

        try:
            self.db.add(db_post) # Add the modified object to the session
            self.db.commit() # Commit changes to the database
            self.db.refresh(db_post) # Refresh the object to reflect latest DB state

            # Re-fetch the post with all necessary relationships eager-loaded for Pydantic response.
            final_db_post = self.get_post_by_id(db_post.post_id)
            if not final_db_post:
                logger.error(f"Failed to retrieve updated post ID: {db_post.post_id} after update.")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve updated post for response."
                )

            logger.info(f"Successfully updated post ID: {post_id}.")
            return final_db_post
        except HTTPException:
            raise # Re-raise HTTP exceptions from validation or authorization
        except Exception as e:
            self.db.rollback() # Rollback DB transaction on error
            logger.exception(f"An unexpected error occurred while updating post ID: {post_id} for user ID: {user_id}.")
            # If a new file was saved but DB transaction failed, delete the new file to prevent orphans.
            if media_file and new_media_filename: # Check if new_media_filename was assigned
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
            # Use the centralized file_manager to delete the associated media file.
            if db_post.media_url:
                file_manager.delete_file(db_post.media_url)

            self.db.delete(db_post) # Delete the post record from the database.
            self.db.commit() # Commit the deletion.
            logger.info(f"Successfully deleted post ID: {post_id}.")
        except HTTPException:
            raise # Re-raise HTTP exceptions from authorization
        except Exception as e:
            self.db.rollback() # Rollback DB transaction on error
            logger.exception(f"Failed to delete post ID: {post_id}. Rolling back transaction.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete post due to a server error: {e}"
            )
