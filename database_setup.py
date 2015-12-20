import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class User(Base):
	__tablename__ = 'user'

	id = Column(Integer, primary_key=True)
	name = Column(String(250), nullable=False)
	email = Column(String)
	picture = Column(String)
	boxers = relationship('Boxer', backref='user')


class Category(Base):
	__tablename__ = 'category'

	id = Column(Integer, primary_key=True)
	name = Column(String(250), nullable=False)
	boxers = relationship('Boxer', backref='category', cascade='all, delete, delete-orphan')
	
	@property
	def serialize(self):
		return {
			'name': self.name,
			'id': self.id,
			'boxers': [b.serialize for b in self.boxers]
		}
	
	

class Boxer(Base):
	__tablename__ = 'boxer'

	name =Column(String(80), nullable = False)
	id = Column(Integer, primary_key = True)
	description = Column(String(250))
	category_id = Column(Integer,ForeignKey('category.id')) 
	user_id = Column(Integer,ForeignKey('user.id'))
	
	@property
	def serialize(self):
		return {
			'name': self.name,
			'description': self.description,
			'id': self.id,
			'category_id': self.category_id
		}


engine = create_engine('sqlite:///boxing.db')
Base.metadata.create_all(engine)


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

# Create first user
User1 = User(name="Bob Arum", email="bob@toprank.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()



#Create Heavyweight category
cat = Category(name = "Heavyweight")

session.add(cat)
session.commit()

boxer1 = Boxer(user_id=1, name = "Joe Frazier", description = "Has a mean left hook.", category = cat)
session.add(boxer1)
session.commit()

boxer1 = Boxer(user_id=1, name = "Muhammad Ali", description = "The Greatest of all time.", category = cat)
session.add(boxer1)
session.commit()



#Create Light Heavyweight category
cat = Category(name = "Light Heavyweight")

session.add(cat)
session.commit()

boxer1 = Boxer(user_id=1, name = "Roy Jones, Jr.", description = "One of the all time greats.", category = cat)
session.add(boxer1)
session.commit()

boxer1 = Boxer(user_id=1, name = "Antonio Tarver", description = "Appeared in one of the 'Rocky' movies.", category = cat)
session.add(boxer1)
session.commit()



#Create Middleweight category
cat = Category(name = "Middleweight")

session.add(cat)
session.commit()

boxer1 = Boxer(user_id=1, name = "Marvelous Marvin Hagler", description = "Highly skilled and powerful.", category = cat)
session.add(boxer1)
session.commit()

boxer1 = Boxer(user_id=1, name = "Sugar Ray Robinson", description = "Elevated boxing to a Sweet Science.", category = cat)
session.add(boxer1)
session.commit()



#Create Welterweight category
cat = Category(name = "Welterweight")

session.add(cat)
session.commit()

boxer1 = Boxer(user_id=1, name = "Manny Pacquiao", description = "Pound for pound best fighter.", category = cat)
session.add(boxer1)
session.commit()

boxer1 = Boxer(user_id=1, name = "Floyd Mayweather", description = "Brilliant defensive fighter.", category = cat)
session.add(boxer1)
session.commit()




