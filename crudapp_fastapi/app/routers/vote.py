from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from .. import models, schemas, oauth2
from ..database import get_db

router = APIRouter(
    prefix="/vote",
    tags=['Vote']
)


# This is a FastAPI router endpoint for handling voting functionality on posts
# It allows users to upvote (add vote) or remove their vote from posts
@router.post("/", status_code=status.HTTP_201_CREATED)
def vote(vote: schemas.Vote, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # First, check if the post that user wants to vote on actually exists in the database
    post = db.query(models.Post).filter(models.Post.id == vote.post_id).first()
    if not post:
        # If post doesn't exist, return 404 error
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with id: {vote.post_id} does not exist")

    # Query to check if the current user has already voted on this specific post
    vote_query = db.query(models.Vote).filter(
        models.Vote.post_id == vote.post_id, models.Vote.user_id == current_user.id)
    found_vote = vote_query.first()

    # If vote.dir == 1, user wants to add an upvote
    if (vote.dir == 1):
        # Check if user has already voted on this post
        if found_vote:
            # If already voted, return conflict error (409)
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"user {current_user.id} has already voted on post {vote.post_id}")
        # Create new vote record and save to database
        new_vote = models.Vote(post_id=vote.post_id, user_id=current_user.id)
        db.add(new_vote)
        db.commit()
        return {"message": "successfully added vote"}
    else:
        # If vote.dir != 1, user wants to remove their vote
        if not found_vote:
            # If no existing vote found, return 404 error
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Vote does not exist")
        # Delete the existing vote from database
        vote_query.delete(synchronize_session=False)
        db.commit()
        return {"message": "successfully deleted vote"}
