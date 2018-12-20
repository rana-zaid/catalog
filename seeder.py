#! /usr/bin/env python3

# Imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime
from database_setup import User, Category, Item, Base

engine = create_engine('sqlite:///catalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# create a dummy user
User1 = User(name="admin",
             email="rno633@gmail.com",
             picture='https://pbs.twimg.com/profile_images/\
                   822101119392481280/GQzHFfLP_400x400.jpg')

session.add(User1)
session.commit()

# categories
category1 = Category(name="Literature & Fiction",
                     user_id=1)

session.add(category1)
session.commit()

item1_1 = Item(name="The Complete Novels of Sherlock Holmes",
               author="Arthur Conan Doyle",
               picture="http://bit.ly/2QVJsf1",
               date=datetime.datetime.now(),
               category=category1,
               user_id=1)

session.add(item1_1)
session.commit()


item2_1 = Item(name="Hooked: How to Build Habit-Forming Products",
               author="Nir Eyal",
               picture="http://bit.ly/2ChzE76",
               date=datetime.datetime.now(),
               category=category1,
               user_id=1)

session.add(item2_1)
session.commit()


category2 = Category(name="Law",
                     user_id=1)

session.add(category2)
session.commit()

item1_2 = Item(name="Business Law for Managers: IIMA Series",
               author="Anurag K Agarwal",
               picture="http://bit.ly/2S5q5gX",
               date=datetime.datetime.now(),
               category=category2,
               user_id=1)

session.add(item1_2)
session.commit()


item2_2 = Item(name="Lectures on Administrative Law",
               author="C. K. Takwani",
               picture="http://bit.ly/2RZC7bO",
               date=datetime.datetime.now(),
               category=category2,
               user_id=1)

session.add(item2_2)
session.commit()


category3 = Category(name="Business & Economics",
                     user_id=1)

session.add(category3)
session.commit()

item1_3 = Item(name="The Design of Everyday Things",
               author="Don Norman",
               picture="http://bit.ly/2A2hcxD",
               date=datetime.datetime.now(),
               category=category3,
               user_id=1)

session.add(item1_3)
session.commit()


item2_3 = Item(name="Zero to One: Note on Start Ups,\
                 or How to Build the Future",
               author="Peter Thiel & Blake Masters",
               picture="http://bit.ly/2QX3WEe",
               date=datetime.datetime.now(),
               category=category3,
               user_id=1)

session.add(item2_3)
session.commit()


category4 = Category(name="Crime, Thriller & Mystery",
                     user_id=1)

session.add(category4)
session.commit()

item1_4 = Item(name="Secret of the Himalayan Treasure",
               author="Divyansh Mundra",
               picture="http://bit.ly/2ElPleZ",
               date=datetime.datetime.now(),
               category=category4,
               user_id=1)

session.add(item1_4)
session.commit()


item2_4 = Item(name="Don't Tell The Governor",
               author="Ravi Subramanian",
               picture="http://bit.ly/2PHuXqq",
               date=datetime.datetime.now(),
               category=category4,
               user_id=1)

session.add(item2_4)
session.commit()
print("added category items!")
