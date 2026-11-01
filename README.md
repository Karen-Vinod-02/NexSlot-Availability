# NexSlot Availability

NexSlot Availability is a resource scheduling platform for organizations that need a clear, reliable way to coordinate shared spaces. It brings availability, reservations, access control, and usage insights together in one application, helping teams plan sessions and meetings while preventing double bookings.

The platform pairs a role-based operations workflow with an optional, locally hosted AI assistant. Its retrieval-augmented generation (RAG) pipeline indexes approved documents or website content and uses those sources to answer questions through a natural-language interface.

## Features

- **Resource coordination:** View availability by date and configurable time slot, and reserve spaces for scheduled activities.
- **Conflict prevention:** Enforce one reservation per space, date, and time slot.
- **Role-based workflows:** Provide tailored access and dashboards for administrators, faculty, and participants.
- **Controlled onboarding:** Let administrators authorize email addresses and manage registration eligibility.
- **Flexible scheduling:** Capture academic subjects, meeting topics, target groups, and guest-speaker details.
- **Operational visibility:** Review booking activity, collect feedback, and inspect usage analytics.
- **Configurable experience:** Set the organization type, booking slots, site identity, logo, and visual theme.
- **Source-grounded assistance:** Optionally index documents and website content for question answering with a local RAG pipeline.

## Technology Stack

- **Backend:** Python, Django
- **Data layer:** MySQL
- **Web interface:** Django templates, Bootstrap 5, Crispy Forms
- **Application serving and static assets:** Gunicorn, WhiteNoise
- **Container support:** Docker
- **AI and retrieval:** Ollama, Qwen 2.5 1.5B, LangChain, Chroma

## Requirements

- Python 3.10 or later
- MySQL 8.0
- pip

The AI assistant is optional; its dependencies and setup are described in [Optional AI Assistant](#optional-ai-assistant).

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/Karen-Vinod-02/NexSlot-Availability.git
cd NexSlot-Availability
```

### 2. Configure MySQL

Create a database and a dedicated application user. Run the following in a MySQL client as an administrator, replacing the example password:

```sql
CREATE DATABASE classroom_availability CHARACTER SET utf8mb4;
CREATE USER 'classroom_user'@'localhost' IDENTIFIED BY 'change-this-password';
GRANT ALL PRIVILEGES ON classroom_availability.* TO 'classroom_user'@'localhost';
```

### 3. Install the application

Create a virtual environment:

```bash
python -m venv .venv
```

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS or Linux
source .venv/bin/activate
```

Activate the environment and install the project dependencies:

```bash
python -m pip install -r requirements.txt
```

On Windows, pip uses a prebuilt `mysqlclient` wheel when one is available for your Python version. If installation falls back to compiling the package, install the Microsoft C++ Build Tools and MariaDB Connector/C, then retry.

### 4. Set environment variables

Configure the application through environment variables. For Windows PowerShell:

```powershell
$env:SECRET_KEY = "replace-with-a-long-random-secret"
$env:DEBUG = "True"
$env:ALLOWED_HOSTS = "127.0.0.1,localhost"
$env:MYSQL_DATABASE = "classroom_availability"
$env:MYSQL_USER = "classroom_user"
$env:MYSQL_PASSWORD = "change-this-password"
$env:MYSQL_HOST = "localhost"
$env:MYSQL_PORT = "3306"
```

Set the equivalent variables in your shell or deployment environment on macOS and Linux. Use a private `SECRET_KEY` and secure database password; never use development credentials in production.

### 5. Apply migrations and start the server

```bash
python manage.py migrate
python manage.py runserver
```

Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/) to access the application.

### 6. Create an administrator

Create the initial administrator account through the Django shell:

```bash
python manage.py shell
```

```python
from classroom.models import User

admin = User(
    username="admin@example.com",
    email="admin@example.com",
    role="Admin",
    is_staff=True,
    is_superuser=True,
)
admin.set_password("replace-with-a-strong-password")
admin.save()
```

Sign in to manage system settings and user onboarding. Administrators can import authorized accounts from a CSV with `email` and `role` columns; `first_name`, `last_name`, `department`, `year`, and `division` are optional. Supported roles are `Admin`, `Faculty`, `Student`, and `Employee`. Use `Student` for academic participants and `Employee` for corporate participants.

## Optional AI Assistant

The assistant runs against a local Ollama service and requires additional Python packages. With the virtual environment active, install:

```bash
python -m pip install langchain-chroma langchain-ollama langchain-core langchain-text-splitters langchain-community pypdf requests beautifulsoup4 urllib3
```

Install and start [Ollama](https://ollama.com/), then download the model used by the application:

```bash
ollama pull qwen2.5:1.5b
```

The application connects to Ollama at `http://localhost:11434`. Administrators can enable or disable the assistant and configure its greeting and website source. In corporate mode, administrators and employees can upload PDF or TXT files for indexing. In college mode, document uploads are available to faculty. The ingestion pipeline splits source material into overlapping chunks, stores embeddings in Chroma, and retrieves relevant passages to ground responses in the indexed content.

## Production

For deployment, set `DEBUG=False`, provide a private `SECRET_KEY`, and restrict `ALLOWED_HOSTS` to the application's hostnames. Use dedicated database credentials, and configure persistent storage and backups for the database and uploaded media. Do not use Django's development server in production; serve the application through a production WSGI server such as Gunicorn.