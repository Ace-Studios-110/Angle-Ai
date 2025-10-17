from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from middlewares.auth import verify_auth_token
from services.upload_plan_service import process_uploaded_plan, extract_business_info_from_plan
import os
import uuid
import tempfile

router = APIRouter()

@router.post("/")
async def upload_business_plan(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(verify_auth_token)
):
    """
    Upload and process a business plan document (does NOT store in database)
    Simply extracts business info and returns it to frontend for session update
    Supports: PDF, DOCX, TXT files
    
    Endpoint: POST /upload-plan (router prefix + "/" = /upload-plan)
    """
    temp_file_path = None
    
    try:
        # Validate file type
        allowed_extensions = ['.pdf', '.docx', '.txt']
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Please upload: {', '.join(allowed_extensions)}"
            )
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        file_content = await file.read()
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=400,
                detail="File too large. Maximum size is 10MB."
            )
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        # Process the uploaded plan
        processed_content = await process_uploaded_plan(temp_file_path, file_extension)
        
        # Extract business information
        business_info = await extract_business_info_from_plan(processed_content)
        
        # Return the extracted business info to frontend
        # Frontend will update the session with this data
        return JSONResponse(content={
            "success": True,
            "message": "Business plan processed successfully!",
            "business_info": business_info,
            "content_preview": processed_content[:500] + "..." if len(processed_content) > 500 else processed_content
        })
                
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading business plan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process business plan: {str(e)}")
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass  # Ignore cleanup errors

# No additional endpoints needed - upload plan is a simple one-time extraction
# Frontend handles applying the extracted business_info to the session
