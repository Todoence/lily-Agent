from fastapi import FastAPI, HTTPException, Request, Body
import os
import time
from dotenv import load_dotenv
from firecrawl import FirecrawlApp
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import re
import json
import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from database import router as db_router
from pydantic import BaseModel
from typing import List
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# Load environment variables
load_dotenv()

app = FastAPI()
# Include the router defined in database.py
app.include_router(db_router)

# Mount the static file directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize the template directory
templates = Jinja2Templates(directory="templates")

# Frontend homepage route, returns index.html
@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

@app.post("/generate_knowledge_base")
async def generate_knowledge_base(
    target_url: str = Body(...),
    file_name: str = Body(...)
):
    """
    Crawl the website content from the target URL and save the Markdown knowledge base to data/knowledge_base/knowledge_base.
    Check if the content is empty during crawling, and return an error if it is.
    Although the interface includes the file_name parameter, it will be fixed to "knowledge_base" by the frontend.
    """
    # Force file_name to "knowledge_base"
    file_name = "knowledge_base"
    
    # If DEBUG_MODE=true is set, return debug result directly
    if os.getenv("DEBUG_MODE", "false").lower() == "true":
        output_file = os.path.join("data", "knowledge_base", file_name)
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        # Return debug info without actual crawling
        return {
            "message": f"(DEBUG) The target website content has been successfully saved to {output_file}",
            "file_path": output_file
        }
    
    # Read Firecrawl API key from environment variable
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing FIRECRAWL_API_KEY in environment.")
    
    # Initialize Firecrawl app
    fire_app = FirecrawlApp(api_key=api_key)
    
    # Set output directory to data/knowledge_base and ensure it exists
    output_folder = os.path.join("data", "knowledge_base")
    os.makedirs(output_folder, exist_ok=True)
    output_file = os.path.join(output_folder, file_name)
    
    # Start crawling the target website
    crawl_status = fire_app.crawl_url(
        target_url,
        params={
            'limit': 10,
            'scrapeOptions': {'formats': ['markdown'], 'onlyMainContent': True}
        },
        poll_interval=30
    )
    
    crawl_id = crawl_status.get('id')
    status = crawl_status.get('status')
    while status != 'completed':
        time.sleep(10)
        crawl_status = fire_app.check_crawl_status(crawl_id)
        status = crawl_status.get('status')
        print(f"current status: {status}")
    
    # Retrieve the crawled Markdown content
    markdown_content = "\n".join([item.get('markdown', '') for item in crawl_status.get('data', [])])
    
    # Check if content is empty
    if not markdown_content.strip():
        raise HTTPException(status_code=400, detail="The crawled markdown content is empty. Aborting.")
    
    # Save to the specified file
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error writing file: {e}")
    
    return {"message": f"The target website content has been successfully saved to {output_file}", "file_path": output_file}

@app.post("/process_knowledge_base")
async def process_knowledge_base(payload: dict = Body(...)):
    """
    Read the Markdown knowledge base from the given file path,
    call DeepSeek to generate a standardized company profile document,
    and save the final result to data/company_profile/company_profile.md.
    Also checks for file existence and whether the content is empty.
    
    Example request body:
    {
      "file_path": "data\\knowledge_base\\knowledge_base"
    }
    """
    file_path = payload.get("file_path")
    if not file_path:
        raise HTTPException(status_code=422, detail="file_path is required.")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found.")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            markdown_content = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {e}")
    
    if not markdown_content.strip():
        raise HTTPException(status_code=400, detail="Markdown content is empty. Aborting API call.")
    
    print(f"Markdown content length: {len(markdown_content)}")
    
    # If debug mode is on, return the existing cached file path without modifying contents
    if os.getenv("DEBUG_MODE", "false").lower() == "true":
        output_folder2 = os.path.join("data", "company_profile")
        os.makedirs(output_folder2, exist_ok=True)
        output_file2 = os.path.join(output_folder2, "company_profile.md")
        return {"message": f"(DEBUG) Standardized company profile not modified. Using existing file: {output_file2}", "output_file": output_file2}
    
    # Set environment variables for DeepSeek API
    os.environ["OPENAI_API_KEY"] = os.getenv("DEEPSEEK_API_KEY")
    os.environ["OPENAI_API_BASE"] = "https://api.deepseek.com"
    
    # Build prompt template
    prompt_template = ChatPromptTemplate.from_template(
        "You are an expert analyst specialized in generating structured company profiles from provided content.\n\n"
        "Extract key information from the markdown content provided below, and generate a standardized company profile document in English. "
        "Please be as detailed as possible. "
        "Include the following sections:\n\n"
        "1. Company Information:\n"
        "- Company Name\n"
        "- Company Website\n"
        "- Industry\n\n"
        "2. Product and Business Information:\n"
        "- Product/Service Offering & Features\n"
        "- Unique Selling Points (USPs)\n"
        "- Typical Use Cases\n\n"
        "3. Value Proposition & Customer Pain Points:\n"
        "- Value Proposition\n"
        "- Customer Pain Points\n\n"
        "4. Target Market and Customer Profile:\n"
        "- Target Industry\n"
        "- Ideal Customer Profile (ICP)\n\n"
        "5. Customer Success and Testimonials:\n"
        "- Case Studies or Testimonials\n\n"
        "Markdown Content:\n\n{markdown_content}"
    )
    
    # Initialize DeepSeek model
    llm = ChatOpenAI(
        model="deepseek-reasoner",
        temperature=0.2,
        max_tokens=3000
    )
    
    # Construct messages
    messages = prompt_template.format_messages(markdown_content=markdown_content)
    
    # Call DeepSeek model to get results
    result = llm.invoke(messages)
    
    # Set output directory to data/company_profile and ensure it exists
    output_folder2 = os.path.join("data", "company_profile")
    os.makedirs(output_folder2, exist_ok=True)
    output_file2 = os.path.join(output_folder2, "company_profile.md")
    
    try:
        with open(output_file2, "w", encoding="utf-8") as f:
            f.write(result.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error writing result file: {e}")
    
    return {"message": f"Standardized company profile created: {output_file2}", "output_file": output_file2}

@app.post("/find_potential_events")
async def find_potential_events(payload: dict = Body(...)):
    """
    1. Read the specified company profile Markdown file
    2. Call DeepSeek to return a structured JSON array with fields:
         - name (string)
         - url (string)
         - category (string) (value: Associations, Exhibitions, News)
    3. Clean the response to remove markdown formatting and save to file (for inspection)
    4. Return parsed JSON data for further database insertion or frontend use

    Example request body:
    {
      "file_path": "data\\company_profile\\company_profile.md"
    }
    """
    file_path = payload.get("file_path")
    if not file_path:
        raise HTTPException(status_code=422, detail="file_path is required.")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Company profile file not found.")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            company_profile = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading company profile file: {e}")
    
    if not company_profile.strip():
        raise HTTPException(status_code=400, detail="Company profile content is empty.")
    
    # If debug mode is on, return existing cached content without modification
    if os.getenv("DEBUG_MODE", "false").lower() == "true":
        output_folder = os.path.join("data", "potential_events")
        os.makedirs(output_folder, exist_ok=True)
        output_file = os.path.join(output_folder, "potential_events.json")
        if os.path.exists(output_file):
            try:
                with open(output_file, "r", encoding="utf-8") as f:
                    cleaned_output = f.read()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error reading potential events file: {e}")
            try:
                events_data = json.loads(cleaned_output)
            except Exception:
                events_data = None
            return {
                "message": f"(DEBUG) Potential events not modified. Using existing file: {output_file}",
                "output_file": output_file,
                "parsed_data": events_data
            }
        else:
            return {
                "message": f"(DEBUG) Potential events file not found. No modification performed.",
                "output_file": output_file,
                "parsed_data": None
            }
    
    # Set environment variables for DeepSeek API
    os.environ["OPENAI_API_KEY"] = os.getenv("DEEPSEEK_API_KEY")
    os.environ["OPENAI_API_BASE"] = "https://api.deepseek.com"
    
    # Build prompt to return clean JSON without extra text or markdown blocks
    prompt_template = ChatPromptTemplate.from_template(
        "You are an expert market analyst specialized in identifying potential event opportunities. "
        "Based on the following company profile information, please provide a structured JSON array of relevant trade associations, industry events, and bodies where target customers are likely to attend (based on public information). "
        "Each event object should have the following fields: "
        "name (string), url (string), and category (string, one of ['Associations', 'Exhibitions', 'News']). "
        "Return only valid JSON with no extra text, no markdown fences, and no additional keys.\n\n"
        "Company Profile Information:\n\n{company_profile}"
    )
    
    # Initialize DeepSeek model
    llm = ChatOpenAI(
        model="deepseek-reasoner",
        temperature=0.2,
        max_tokens=3000
    )
    
    messages = prompt_template.format_messages(company_profile=company_profile)
    result = llm.invoke(messages)
    
    # Clean returned text by removing markdown code blocks
    raw_output = result.content.strip()
    cleaned_output = re.sub(r"^```json\s*", "", raw_output)
    cleaned_output = re.sub(r"\s*```$", "", cleaned_output)
    
    # Parse cleaned JSON
    try:
        events_data = json.loads(cleaned_output)
        if not isinstance(events_data, list):
            raise ValueError("LLM response JSON is not a list.")
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"DeepSeek response is not valid JSON: {e}")

    # Save the cleaning results to a file for subsequent inspection
    output_folder = os.path.join("data", "potential_events")
    os.makedirs(output_folder, exist_ok=True)
    output_file = os.path.join(output_folder, "potential_events.json")
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(cleaned_output)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error writing potential events file: {e}")
    
    return {
        "message": f"Potential events information saved to {output_file}",
        "output_file": output_file,
        "parsed_data": events_data
    }

@app.post("/extract_companies")
async def extract_companies_from_file(payload: dict = Body(...)):
    """
    Endpoint description:
    1. Receives a parameter 'json_file_path', e.g., "data\\potential_events\\potential_events.json", and reads the JSON data in the file (should be a list containing URLs).
    2. Extracts all URLs from the JSON data (deduplicated).
    3. If there are more than 10 URLs, only the first 10 will be used; calls Firecrawl's extract API to extract company names from the pages, returning a 'companies' field with a list of strings.
    4. Saves the extracted result as a JSON file under the data/potential_customer directory.
    5. Returns the extraction result and file path.
    """
    json_file_path = payload.get("json_file_path")
    if not json_file_path:
        raise HTTPException(status_code=422, detail="json_file_path is required.")
    
    if not os.path.exists(json_file_path):
        raise HTTPException(status_code=404, detail=f"File '{json_file_path}' not found.")
    
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            events_data = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading JSON file: {e}")
    
    if not isinstance(events_data, list):
        raise HTTPException(status_code=400, detail="JSON content is not a list.")
    
    # Extract all URLs (deduplicated)
    urls = list({ event.get("url") for event in events_data if event.get("url") })
    if not urls:
        raise HTTPException(status_code=400, detail="No valid URLs found in JSON data.")
    
    # Limit to first 10 URLs if more than 10
    if len(urls) > 10:
        urls = urls[:10]
    
    # Initialize Firecrawl app (ensure FIRECRAWL_API_KEY is set in the environment)
    API_KEY = os.getenv("FIRECRAWL_API_KEY")
    if not API_KEY:
        raise HTTPException(status_code=500, detail="FIRECRAWL_API_KEY not set in environment.")
    fire_app = FirecrawlApp(api_key=API_KEY)
    
    # Internal schema definition for extraction result
    class ExtractSchema(BaseModel):
        companies: List[str]
    
    options = {
        "prompt": "Extract company names from all pages.",
        "schema": ExtractSchema.model_json_schema(),
        "enable_web_search": False  # Disable web search to save time
    }
    
    # Set output directory data/potential_customer and ensure it exists
    output_folder = os.path.join("data", "potential_customer")
    os.makedirs(output_folder, exist_ok=True)
    output_file = os.path.join(output_folder, "potential_customer.json")
    
    # If debug mode is enabled, return cached content (no modification)
    if os.getenv("DEBUG_MODE", "false").lower() == "true":
        if os.path.exists(output_file):
            try:
                with open(output_file, "r", encoding="utf-8") as f:
                    cached_content = f.read()
                parsed_data = json.loads(cached_content)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error reading cached file: {e}")
            return {
                "message": f"(DEBUG) Using existing potential customer file: {output_file}",
                "output_file": output_file,
                "data": parsed_data
            }
        else:
            return {
                "message": f"(DEBUG) Potential customer file not found. No modification performed.",
                "output_file": output_file,
                "data": None
            }
    
    # Call Firecrawl extract API to extract company names
    try:
        result = fire_app.extract(urls, options)
        if isinstance(result, str):
            result = json.loads(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during extraction: {e}")
    
    # Save extraction result to file
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error writing JSON file: {e}")
    
    return {
        "message": "Extraction completed.",
        "output_file": output_file,
        "data": result
    }

@app.post("/prioritize_companies")
async def prioritize_companies(payload: dict = Body(...)):
    """
    Endpoint description:
    1. Reads potential customer data from potential_customer.json,
       and company profile information from company_profile.md.
    2. Uses DeepSeek API to prioritize these companies, analyzing public data,
       and ranks them based on revenue, company size, and industry fit (higher revenue, larger size, and better fit rank higher),
       skipping fake or non-company entries;
       Also identifies key decision-makers and returns their name, title, email, phone, and LinkedIn Sales Navigator link.
       For stakeholder_link, return an empty string if not found. Do not fabricate data.
    3. Returns a strict JSON format with no extra text or markdown symbols.
    4. The output JSON array should contain the following fields for each object:
         - company_name (string)
         - industry (string)
         - revenue (string)
         - size (string)
         - stakeholder_name (string)
         - stakeholder_position (string)
         - stakeholder_email (string)
         - stakeholder_phone (string)
         - stakeholder_link (string)
         - reasoning (string): one to two sentences explaining the prioritization.
    5. If there are more than 50 valid companies, only the top 50 prioritized ones are returned; otherwise, return all.
    6. Save the result returned by DeepSeek to data/prioritized_companies/prioritized_companies.json.
    
    Request body example:
    {
       "potential_customer_path": "data\\potential_customer\\potential_customer.json",
       "company_profile_path": "data\\company_profile\\company_profile.md"
    }
    """
    potential_customer_path = payload.get("potential_customer_path")
    company_profile_path = payload.get("company_profile_path")
    if not potential_customer_path:
        raise HTTPException(status_code=422, detail="potential_customer_path is required.")
    if not company_profile_path:
        raise HTTPException(status_code=422, detail="company_profile_path is required.")
    
    # Check if files exist
    if not os.path.exists(potential_customer_path):
        raise HTTPException(status_code=404, detail=f"File '{potential_customer_path}' not found.")
    if not os.path.exists(company_profile_path):
        raise HTTPException(status_code=404, detail=f"File '{company_profile_path}' not found.")
    
    # Read potential customer JSON data
    try:
        with open(potential_customer_path, "r", encoding="utf-8") as f:
            potential_data = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading potential customer JSON file: {e}")
    
    # Read company profile Markdown content
    try:
        with open(company_profile_path, "r", encoding="utf-8") as f:
            company_profile = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading company profile file: {e}")
    
    # Convert potential customer data to string for prompt use
    potential_data_str = json.dumps(potential_data, ensure_ascii=False, indent=2)
    
    # If debug mode is enabled, return existing cache without modification
    if os.getenv("DEBUG_MODE", "false").lower() == "true":
        output_folder = os.path.join("data", "prioritized_companies")
        os.makedirs(output_folder, exist_ok=True)
        output_file = os.path.join(output_folder, "prioritized_companies.json")
        if os.path.exists(output_file):
            try:
                with open(output_file, "r", encoding="utf-8") as f:
                    cached_content = f.read()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error reading cached file: {e}")
            return {
                "message": f"(DEBUG) Using existing prioritized companies file: {output_file}",
                "output_file": output_file,
                "raw_result": cached_content
            }
        else:
            return {
                "message": f"(DEBUG) Prioritized companies file not found. No modification performed.",
                "output_file": output_file,
                "raw_result": ""
            }
    
    # Construct DeepSeek prompt
    prompt_template = ChatPromptTemplate.from_template(
        "You are a market research expert. Based on the following company profile information and potential customer data, "
        "analyze public data to prioritize the potential customer companies. Assess each company on approximate revenue, "
        "company size, industry fit, and overall alignment with our products. Ensure that companies with higher revenue, "
        "larger scale, and better industry fit are ranked higher. Skip any entry that appears to be fake or not a legitimate company. "
        "For each valid company, locate key decision-makers and return specific names along with their positions, email addresses, and phone numbers. "
        "For the field stakeholder_link, search for the candidate's LinkedIn Sales Navigator profile link; if not found, return an empty string without fabricating data. "
        "Return the results strictly as valid JSON with no extra text, explanations, or markdown formatting. "
        "The output should be a JSON array sorted by priority (highest priority first), where each object contains the following fields:\n"
        "  - company_name (string)\n"
        "  - industry (string)\n"
        "  - revenue (string)\n"
        "  - size (string)\n"
        "  - stakeholder_name (string)\n"
        "  - stakeholder_position (string)\n"
        "  - stakeholder_email (string)\n"
        "  - stakeholder_phone (string)\n"
        "  - stakeholder_link (string)\n"
        "  - reasoning (string): one to two sentences explaining the prioritization.\n\n"
        "Please analyze all provided companies and do not limit your output to 10. If there are more than 50 valid companies, output only the top 50 prioritized results; otherwise, output all.\n\n"
        "Company Profile Information:\n{company_profile}\n\n"
        "Potential Customer Data:\n{potential_data}"
    )
    
    prompt = prompt_template.format_prompt(
        company_profile=company_profile,
        potential_data=potential_data_str
    )
    
    # Set DeepSeek API environment variables
    os.environ["OPENAI_API_KEY"] = os.getenv("DEEPSEEK_API_KEY")
    os.environ["OPENAI_API_BASE"] = "https://api.deepseek.com"
    
    # Initialize DeepSeek model
    llm = ChatOpenAI(
        model="deepseek-reasoner",
        temperature=0.2,
        max_tokens=5000
    )
    
    try:
        result = llm.invoke(prompt.to_messages())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during DeepSeek call: {e}")
    
    # Clean the returned text, remove possible ```json and ```
    raw_output = result.content.strip()
    cleaned_output = re.sub(r"^```json\s*", "", raw_output)
    cleaned_output = re.sub(r"\s*```$", "", cleaned_output)
    
    # Save cleaned result to file
    output_folder = os.path.join("data", "prioritized_companies")
    os.makedirs(output_folder, exist_ok=True)
    output_file = os.path.join(output_folder, "prioritized_companies.json")
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(cleaned_output)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error writing prioritized companies JSON file: {e}")
    
    return {
        "message": "Prioritization completed.",
        "output_file": output_file,
        "raw_result": cleaned_output
    }


# Define the Pydantic model for company information
class CompanyInfo(BaseModel):
    company_name: str
    industry: str
    revenue: str
    size: str
    stakeholder_name: str
    stakeholder_position: str
    stakeholder_email: str
    stakeholder_phone: str
    stakeholder_link: str
    reasoning: str

@app.post("/generate_outreach_email")
async def generate_outreach_email(company: CompanyInfo = Body(...)):
    """
    Endpoint Description:
    1. Accepts a single company information object from the frontend, with the following example format:
       {
         "company_name": "Honeywell",
         "industry": "Aerospace, Industrial Manufacturing",
         "revenue": "$35.5B",
         "size": "110,000 employees",
         "stakeholder_name": "James Carter",
         "stakeholder_position": "Director of Materials Procurement",
         "stakeholder_email": "james.carter@honeywell.com",
         "stakeholder_phone": "+1-480-257-3201",
         "stakeholder_link": "https://www.linkedin.com/sales/nav/james-carter-honeywell",
         "reasoning": "High revenue and strong alignment with aerospace/industrial applications requiring durable surface protection."
       }
    2. Reads background information from the knowledge base file (e.g., data/company_profile/company_profile.md),
       including company history, core products, value propositions, etc.
    3. Constructs a prompt requesting DeepSeek (or ChatOpenAI) to generate a personalized outreach email,
       referencing company background and customer data, including a professional opening, targeted product value,
       and a clear call-to-action. Output must be plain text.
    4. Saves the generated result to a JSON file and returns the JSON response.
    """
    # 1. Read the knowledge base file
    knowledge_base_path = os.path.join("data", "company_profile", "company_profile.md")
    if not os.path.exists(knowledge_base_path):
        raise HTTPException(status_code=404, detail=f"Knowledge base file '{knowledge_base_path}' not found.")
    try:
        with open(knowledge_base_path, "r", encoding="utf-8") as f:
            company_profile = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading knowledge base file: {e}")

    # 2. Construct the prompt for email generation (format the company object using json.dumps)
    prompt_text = (
        "You are a sales outreach expert. Our company has the following profile:\n\n"
        f"{company_profile}\n\n"
        "The potential customer company information is as follows:\n\n"
        f"{json.dumps(company.dict(), indent=2, ensure_ascii=False)}\n\n"
        "Based on the above information, plus deep search potential customer company information in public, "
        "draft a personalized outreach email that is professional, engaging, and tailored to the potential customer. "
        "The email should reference specific details from both our company profile and the potential customer's data, "
        "explain why our product is a good fit for them, and include a clear call to action. "
        "Output the email as plain text with no additional commentary."
    )

    # 3. Set DeepSeek API environment variables
    API_KEY = os.getenv("DEEPSEEK_API_KEY")
    if not API_KEY:
        raise HTTPException(status_code=500, detail="DEEPSEEK_API_KEY not set in environment.")
    os.environ["OPENAI_API_KEY"] = API_KEY
    os.environ["OPENAI_API_BASE"] = "https://api.deepseek.com"

    # 4. Initialize the DeepSeek model
    try:
        email_model = ChatOpenAI(
            model_name="deepseek-chat",  # Adjust model name if needed
            temperature=0.3,
            max_tokens=1000
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing email model: {e}")

    # 5. Construct messages and call the model to generate the email
    messages = [{"role": "system", "content": prompt_text}]
    try:
        response = email_model.invoke(messages)
        email_text = response.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating outreach email: {e}")

    # 6. Construct the return result
    output = {
        "message": "Personalized outreach email generated.",
        "email": email_text
    }

    # 7. Save the result to a JSON file
    try:
        with open("outreach_email.json", "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving output to JSON file: {e}")

    return output


@app.get("/view_company_profile")
async def view_company_profile():
    file_path = os.path.join("data", "company_profile", "company_profile.md")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Company profile not found.")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {e}")
    return {"content": content}

@app.get("/view_potential_events")
async def view_potential_events():
    file_path = os.path.join("data", "potential_events", "potential_events.json")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Potential events file not found.")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {e}")
    return {"content": content}

@app.get("/view_potential_customer")
async def view_potential_customer():
    file_path = os.path.join("data", "potential_customer", "potential_customer.json")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Potential customer file not found.")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {e}")
    return {"content": content}

@app.get("/view_prioritized_companies")
async def view_prioritized_companies():
    file_path = os.path.join("data", "prioritized_companies", "prioritized_companies.json")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Prioritized companies file not found.")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {e}")
    return {"content": content}

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})
