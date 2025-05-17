from fastapi import APIRouter, HTTPException
import os, json, datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()  # Load .env file

# Retrieve Neon database connection string from environment variables
DATABASE_URL = os.getenv("NEON_DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("NEON_DATABASE_URL not set in environment variables.")

# Create database engine and session
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the database model for the 'potential_events' table
class PotentialEvent(Base):
    __tablename__ = "potential_events"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    category = Column(String, nullable=False)  # Associations / Exhibitions / News
    root_url = Column(String, nullable=False)  # Root URL of the company that initiated the query
    create_time = Column('create_time', DateTime, default=datetime.datetime.utcnow)


# Uncomment the following line to automatically create the table on first run
# Base.metadata.create_all(bind=engine)

router = APIRouter()

@router.post("/store_events_in_db")
async def store_events_in_db(file_path: str, root_url: str):
    """
    Reads JSON data (potential events) from the specified file path,
    and inserts each record into the 'potential_events' table in the Neon database.
    
    Parameters:
    - file_path: Path to the JSON file (e.g., data/potential_events/potential_events.json)
    - root_url: The root URL of the company initiating the query (e.g., https://www.dupont.com/brands/tedlar.html)
    
    Returns:
    - Information on the number of successfully inserted records
    """
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="JSON file not found.")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading JSON file: {e}")
    
    if not isinstance(json_data, list):
        raise HTTPException(status_code=400, detail="JSON content is not a list.")
    
    db = SessionLocal()
    inserted_count = 0
    try:
        for item in json_data:
            # Check required fields
            if not all(k in item for k in ("name", "url", "category")):
                continue  # Skip incomplete data
            event = PotentialEvent(
                name=item["name"],
                url=item["url"],
                category=item["category"],
                root_url=root_url,
                create_time=datetime.datetime.utcnow()
            )
            db.add(event)
            inserted_count += 1
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error inserting records into database: {e}")
    finally:
        db.close()
    
    return {"message": f"Inserted {inserted_count} events into the database."}

# Define the database model for the 'potential_customer' table
class PotentialCustomer(Base):
    __tablename__ = "potential_customer"
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(100), nullable=False)
    industry = Column(String(100), nullable=False)
    revenue = Column(String(50), nullable=False)
    size = Column(String(20), nullable=False)
    stakeholder_name = Column(String(30), nullable=True)
    stakeholder_position = Column(String(30), nullable=True)
    stakeholder_email = Column(String(100), nullable=True)
    stakeholder_phone = Column(String(50), nullable=True)
    stakeholder_link = Column(String(200), nullable=True)  
    reasoning = Column(String(500), nullable=True)
    create_time = Column(DateTime, default=datetime.datetime.utcnow)


@router.post("/store_prioritized_companies_in_db")
async def store_prioritized_companies_in_db(file_path: str):
    """
    Reads JSON data from the specified file path (e.g., data\\prioritized_companies\\prioritized_companies.json),
    and inserts each record into the 'potential_customer' table.

    Table schema:
      - company_name
      - industry
      - revenue
      - size
      - stakeholder_name
      - stakeholder_position
      - stakeholder_email
      - stakeholder_phone
      - reasoning
      - create_time
    """
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File '{file_path}' not found.")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading JSON file: {e}")
    
    if not isinstance(json_data, list):
        raise HTTPException(status_code=400, detail="JSON content is not a list.")
    
    db = SessionLocal()
    inserted_count = 0
    try:
        for item in json_data:
            # Ensure the required fields exist in item, otherwise skip or use defaults
            required_keys = [
                "company_name",
                "industry",
                "revenue",
                "size",
                "stakeholder_name",
                "stakeholder_position",
                "stakeholder_email",
                "stakeholder_phone",
                "reasoning"
            ]
            # Skip incomplete records
            if not all(k in item for k in required_keys):
                continue
            
            customer = PotentialCustomer(
                company_name=item.get("company_name", ""),
                industry=item.get("industry", ""),
                revenue=item.get("revenue", ""),
                size=item.get("size", ""),
                stakeholder_name=item.get("stakeholder_name", ""),
                stakeholder_position=item.get("stakeholder_position", ""),
                stakeholder_email=item.get("stakeholder_email", ""),
                stakeholder_phone=item.get("stakeholder_phone", ""),
                stakeholder_link=item.get("stakeholder_link", ""),
                reasoning=item.get("reasoning", ""),
                create_time=datetime.datetime.utcnow()
            )
            db.add(customer)
            inserted_count += 1
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error inserting records into potential_customer table: {e}")
    finally:
        db.close()
    
    return {"message": f"Inserted {inserted_count} records into the potential_customer table."}
