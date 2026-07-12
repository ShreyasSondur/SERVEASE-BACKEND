from fastapi import APIRouter, BackgroundTasks, status
from app.schemas.contact import ContactForm
from app.utils.email import send_contact_email

router = APIRouter()

@router.post("/submit", status_code=status.HTTP_200_OK)
def submit_contact_form(form_data: ContactForm, background_tasks: BackgroundTasks) -> dict:
    background_tasks.add_task(
        send_contact_email,
        first_name=form_data.first_name,
        last_name=form_data.last_name,
        email=form_data.email,
        message=form_data.message
    )
    return {"detail": "Inquiry submitted successfully. We will be in touch soon!"}
