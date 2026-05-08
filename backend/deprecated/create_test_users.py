from backend.database import SessionLocal, pwd_context, engine
from backend import models

models.Base.metadata.create_all(bind=engine)

db = SessionLocal()
user = db.query(models.User).filter(models.User.email == 'test@test.com').first()
if not user:
    user = models.User(
        email='test@test.com', 
        hashed_password=pwd_context.hash('test123'), 
        role=models.UserRole.DENTISTE, 
        nom_complet='Test Doctor',
        is_active=True
    )
    db.add(user)
    db.commit()
    print('User created: test@test.com / test123')
else:
    user.hashed_password = pwd_context.hash('test123')
    user.is_active = True
    db.commit()
    print('User updated: test@test.com / test123')

# Create a second user for isolation test
user2 = db.query(models.User).filter(models.User.email == 'hacker@test.com').first()
if not user2:
    user2 = models.User(
        email='hacker@test.com', 
        hashed_password=pwd_context.hash('hacker123'), 
        role=models.UserRole.DENTISTE, 
        nom_complet='Evil Doctor',
        is_active=True
    )
    db.add(user2)
    db.commit()
    print('User created: hacker@test.com / hacker123')

db.close()
