import os
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Table, Text, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, relationship
from contextlib import contextmanager
from datetime import datetime
import pytz


from dotenv import load_dotenv
load_dotenv()

cst_time_zone = pytz.timezone('America/Chicago')

Base = declarative_base()

SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')


class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True)
    full_name = Column(String)
    email = Column(String, index=True)
    activities = relationship(
        "Activity", secondary="user_activities", back_populates="users"
    )
    prizes = relationship(
        "Prize", secondary="user_prizes", back_populates="users"
    )

    def total_points(self, session):
        # Summing points for each unique activity achieved
        total_activity_points = 0
        activity_claims = session.query(UserActivity).filter(UserActivity.user_id == self.id).all()
        for claim in activity_claims:
            activity = session.query(Activity).filter(Activity.id == claim.activity_id).first()
            if activity:
                total_activity_points += activity.points

        # Summing cost for each unique prize claimed
        total_prize_cost = 0
        prize_claims = session.query(UserPrize).filter(UserPrize.user_id == self.id).all()
        for claim in prize_claims:
            prize = session.query(Prize).filter(Prize.id == claim.prize_id).first()
            if prize:
                total_prize_cost += prize.cost

        return total_activity_points - total_prize_cost
    
class Activity(Base):
    __tablename__ = 'activities'
    id = Column(Integer, primary_key=True, autoincrement=True)
    emoji = Column(String, index=True)
    points = Column(Float)
    message = Column(String)
    title = Column(String)
    description = Column(String)
    admin_reward = Column(Boolean, default=False)
    rewards_to_poster  = Column(Boolean, default=False)
    users = relationship(
        "User", 
        secondary="user_activities",
        back_populates="activities",

    )
    def to_dict(self):
        return {
            "emoji":self.emoji,
            "points":self.points,
            "message":self.message,
            "title":self.title,
            "description":self.description,
            "admin_reward":self.admin_reward,
            "rewards_to_poster":self.rewards_to_poster

        }

    def delete(self, session):
        session.query(UserActivity).filter(UserActivity.activity_id == self.id).delete()
        session.delete(self)

class Prize(Base):
    __tablename__ = 'prizes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    cost = Column(Integer)
    name = Column(String)
    description = Column(Text)
    win_message = Column(Text)
    users = relationship(
        "User",
        secondary="user_prizes",
        back_populates="prizes",
        
    )
    def delete(self, session):
        session.query(UserPrize).filter(UserPrize.prize_id == self.id).delete()
        session.delete(self)


class UserActivity(Base):
    __tablename__ = 'user_activities'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.id'))
    activity_id = Column(Integer, ForeignKey('activities.id'))
    date_achieved = Column(DateTime, default=lambda: datetime.now(tz=cst_time_zone))
    reaction_item_ts = Column(String, nullable=True)


class UserPrize(Base):
    __tablename__ = 'user_prizes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.id'))
    prize_id = Column(Integer, ForeignKey('prizes.id'))
    date_claimed = Column(DateTime, default=lambda: datetime.now(tz=cst_time_zone))


# create an engine
engine = create_engine(SQLALCHEMY_DATABASE_URI)

# create all tables
Base.metadata.create_all(engine)

Session = scoped_session(sessionmaker(bind=engine))

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
