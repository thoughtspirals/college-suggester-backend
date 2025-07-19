# College Suggester Backend

A powerful FastAPI-based backend service that provides intelligent college recommendations for students based on their academic performance, preferences, and various criteria. This API processes MH-CET and other entrance exam data to suggest the best college matches.

## 🚀 Features

- **Intelligent College Matching** - Advanced algorithms to suggest colleges based on student criteria
- **PDF Data Processing** - Automated parsing of college admission data from PDF documents
- **RESTful API** - Clean and well-documented endpoints
- **Database Integration** - SQLite database for efficient data storage and retrieval
- **Real-time Suggestions** - Fast response times for college recommendations
- **Comprehensive College Data** - Detailed information about colleges, courses, and admission criteria
- **Region-based Filtering** - Location-specific college recommendations

## 🛠️ Tech Stack

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **SQLite** - Lightweight database for development
- **Pydantic** - Data validation and serialization
- **Python 3.8+** - Programming language
- **PDF Processing** - Custom PDF parsing utilities
- **Uvicorn** - ASGI server for running the application

## 📦 Project Structure

```
app/
├── __init__.py
├── main.py                 # FastAPI application entry point
├── database.py             # Database configuration and connection
├── models.py              # SQLAlchemy database models
├── schemas.py             # Pydantic models for request/response
├── crud.py                # Database operations (Create, Read, Update, Delete)
├── routes.py              # API route definitions
├── apis/
│   ├── __init__.py
│   └── college_suggestion.py  # College suggestion API endpoints
├── utils/
│   └── pdf_parser.py      # PDF processing utilities
└── data/                  # College data files
    ├── _final.pdf
    ├── available_seats_cap1.pdf
    └── mh-cet-cap-1.pdf

# Utility Scripts
├── create_tables.py       # Database table creation
├── load_colleges.py       # Load college data into database
├── load_pdf_data.py      # Process and load PDF data
├── load_regions.py       # Load region/location data
├── check_data.py         # Data validation and verification
├── test_insert.py        # Test database operations
└── view_data.py          # View database contents
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/thoughtspirals/college-suggester-backend.git
   cd college-suggester-backend
   ```

2. **Create and activate virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database**
   ```bash
   python create_tables.py
   ```

5. **Load initial data**
   ```bash
   # Load regions/locations
   python load_regions.py
   
   # Load college data
   python load_colleges.py
   
   # Process and load PDF data
   python load_pdf_data.py
   ```

6. **Start the development server**
   ```bash
   uvicorn app.main:app --reload
   ```

7. **Access the API**
   - API: http://localhost:8000
   - Interactive Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 📋 API Endpoints

### College Suggestions
- `POST /suggest` - Get college recommendations based on student criteria
- `GET /colleges` - Retrieve all colleges with optional filtering
- `GET /colleges/{college_id}` - Get specific college details

### Data Management
- `GET /regions` - Get available regions/locations
- `GET /courses` - Get available courses
- `GET /stats` - Get database statistics

### Health Check
- `GET /health` - API health status

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the root directory:

```env
# Database
DATABASE_URL=sqlite:///./college_suggester.db

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# CORS Settings
ALLOWED_ORIGINS=["http://localhost:4200", "https://yourdomain.com"]
```

### Database Configuration
The application uses SQLite by default. To use PostgreSQL or MySQL:

1. Install the appropriate driver
2. Update `DATABASE_URL` in environment variables
3. Modify `database.py` if needed

## 📊 Data Processing

### PDF Data Sources
The application processes several PDF files containing college admission data:

- **mh-cet-cap-1.pdf** - MH-CET CAP round 1 data
- **available_seats_cap1.pdf** - Available seats information
- **_final.pdf** - Final admission data

### Data Loading Scripts

1. **create_tables.py** - Initialize database schema
2. **load_regions.py** - Load geographical regions
3. **load_colleges.py** - Load college information
4. **load_pdf_data.py** - Process PDF files and extract data

### Utility Scripts

- **check_data.py** - Validate data integrity
- **view_data.py** - Browse database contents
- **test_insert.py** - Test database operations

## 🧮 College Suggestion Algorithm

The recommendation system considers:

1. **Academic Performance** - Marks, percentile, rank
2. **Course Preferences** - Desired field of study
3. **Location Preferences** - Preferred regions/cities
4. **College Type** - Government, private, autonomous
5. **Fees Constraints** - Budget considerations
6. **Seat Availability** - Real-time availability data

## 🔍 API Usage Examples

### Get College Suggestions
```bash
curl -X POST "http://localhost:8000/suggest" \
     -H "Content-Type: application/json" \
     -d '{
       "marks": 85,
       "category": "OPEN",
       "preferred_region": "Mumbai",
       "course_preference": "Computer Engineering"
     }'
```

### Get All Colleges
```bash
curl -X GET "http://localhost:8000/colleges?region=Pune&course=IT"
```

### Health Check
```bash
curl -X GET "http://localhost:8000/health"
```

## 🧪 Testing

Run tests using pytest:
```bash
# Install testing dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/

# Run with coverage
pytest --cov=app tests/
```

## 🚀 Deployment

### Local Production
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Docker Deployment
```bash
# Build image
docker build -t college-suggester-backend .

# Run container
docker run -p 8000:8000 college-suggester-backend
```

### Cloud Deployment Options

#### Heroku
```bash
# Install Heroku CLI
pip install gunicorn
echo "web: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker" > Procfile
git add . && git commit -m "Deploy to Heroku"
heroku create your-app-name
git push heroku main
```

#### Railway/Render
- Connect GitHub repository
- Set build command: `pip install -r requirements.txt`
- Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## 📈 Performance Optimization

- **Database Indexing** - Optimized queries with proper indexes
- **Caching** - Redis integration for frequently accessed data
- **Async Operations** - Non-blocking database operations
- **Connection Pooling** - Efficient database connection management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add type hints to all functions
- Write comprehensive docstrings
- Add unit tests for new features
- Update API documentation

## 🐛 Troubleshooting

### Common Issues

1. **Database not found**
   ```bash
   python create_tables.py
   ```

2. **Import errors**
   ```bash
   pip install -r requirements.txt
   ```

3. **PDF processing errors**
   - Ensure PDF files are in the `app/data/` directory
   - Check file permissions

4. **Port already in use**
   ```bash
   uvicorn app.main:app --port 8001
   ```

## 📊 Database Schema

### Main Tables
- **colleges** - College information and details
- **regions** - Geographical regions and locations
- **admission_data** - Historical admission data
- **courses** - Available courses and programs
- **seat_matrix** - Seat availability information

## 🔮 Future Enhancements

- [ ] Machine Learning-based recommendations
- [ ] Real-time seat availability updates
- [ ] Integration with multiple entrance exams
- [ ] Advanced filtering and sorting options
- [ ] User preference learning
- [ ] College comparison features
- [ ] Mobile app API optimization

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Your Team** - Initial work - [thoughtspirals](https://github.com/thoughtspirals)

## 🙏 Acknowledgments

- FastAPI community for the excellent framework
- SQLAlchemy team for the robust ORM
- College data sources and educational institutions
- Open source Python community

## 📞 Support

For support, email your-email@domain.com or create an issue in this repository.

---

**Built with ❤️ to help students find their perfect college match**
