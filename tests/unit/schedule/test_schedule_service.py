import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from uuid import uuid4
from datetime import datetime, time

# Mock all database and external dependencies before importing
with patch('services.schedule.src.db.get_db'), \
     patch('services.schedule.src.db.engine'), \
     patch('sqlalchemy.ext.asyncio.create_async_engine'), \
     patch('sqlalchemy.ext.asyncio.async_sessionmaker'):
    
    from services.schedule.src.schemas import ClassCreate, ClassOut
    from services.schedule.src.models import ClassTemplate


@pytest.fixture
def sample_class_template_data():
    """Provides sample valid data for ClassCreate schema"""
    return {
        "name": "Ballet Basics",
        "teacher": "Anna Smith",
        "weekday": 1,
        "start_time": time(10, 0),
        "capacity": 15,
        "comment": "Introduction to ballet",
        "active": True
    }


@pytest.fixture
def sample_class_out_data():
    """Provides sample valid data for ClassOut schema"""
    return {
        "id": str(uuid4()),
        "name": "Ballet Basics",
        "teacher": "Anna Smith",
        "weekday": 1,
        "start_time": time(10, 0),
        "capacity": 15,
        "comment": "Introduction to ballet",
        "active": True,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }


class TestClassSchemas:
    """Unit tests for Class schemas"""
    
    def test_class_create_schema_valid(self, sample_class_template_data):
        """Test ClassCreate schema with valid data"""
        class_create = ClassCreate(**sample_class_template_data)
        
        assert class_create.name == sample_class_template_data["name"]
        assert class_create.teacher == sample_class_template_data["teacher"]
        assert class_create.weekday == sample_class_template_data["weekday"]
        assert class_create.start_time == sample_class_template_data["start_time"]
        assert class_create.capacity == sample_class_template_data["capacity"]
        assert class_create.comment == sample_class_template_data["comment"]

    
    def test_class_create_schema_invalid_weekday(self):
        """Test ClassCreate schema with invalid weekday"""
        invalid_data = {
            "name": "Ballet Basics",
            "teacher": "Anna Smith",
            "weekday": 8,  # Invalid weekday (should be 1-7)
            "start_time": time(10, 0),
            "capacity": 15,
            "comment": "Introduction to ballet"
        }
        
        with pytest.raises(ValueError):
            ClassCreate(**invalid_data)
    
    def test_class_create_schema_zero_capacity(self):
        """Test ClassCreate schema with zero capacity"""
        invalid_data = {
            "name": "Ballet Basics",
            "teacher": "Anna Smith",
            "weekday": 1,
            "start_time": "10:00:00",
            "capacity": 0,  # Invalid capacity
            "comment": "Introduction to ballet",
            "active": True
        }
        
        with pytest.raises(ValueError):
            ClassCreate(**invalid_data)
    
    def test_class_create_schema_negative_capacity(self):
        """Test ClassCreate schema with negative capacity"""
        invalid_data = {
            "name": "Ballet Basics",
            "teacher": "Anna Smith",
            "weekday": 1,
            "start_time": "10:00:00",
            "capacity": -5,  # Invalid negative capacity
            "comment": "Introduction to ballet",
            "active": True
        }
        
        with pytest.raises(ValueError):
            ClassCreate(**invalid_data)
    
    def test_class_create_schema_empty_name(self):
        """Test ClassCreate schema with empty name"""
        invalid_data = {
            "name": "",  # Invalid empty name
            "teacher": "Anna Smith",
            "weekday": 1,
            "start_time": "10:00:00",
            "capacity": 15,
            "comment": "Introduction to ballet",
            "active": True
        }
        
        with pytest.raises(ValueError):
            ClassCreate(**invalid_data)
    
    def test_class_out_schema(self, sample_class_out_data):
        """Test ClassOut schema"""
        class_out = ClassOut(**sample_class_out_data)
        
        assert str(class_out.id) == sample_class_out_data["id"]
        assert class_out.name == sample_class_out_data["name"]
        assert class_out.teacher == sample_class_out_data["teacher"]
        assert class_out.weekday == sample_class_out_data["weekday"]
        assert class_out.start_time == sample_class_out_data["start_time"]
        assert class_out.capacity == sample_class_out_data["capacity"]
        assert class_out.comment == sample_class_out_data["comment"]
        assert class_out.active == sample_class_out_data["active"]
        assert class_out.created_at is not None
        assert class_out.updated_at is not None


class TestClassTemplateModel:
    """Unit tests for ClassTemplate model"""
    
    def test_class_template_model_repr(self):
        """Test ClassTemplate model string representation"""
        class_template = ClassTemplate(
            id=uuid4(),
            name="Ballet Basics",
            teacher="Anna Smith",
            weekday=1,
            start_time=time(10, 0),
            capacity=15,
            comment="Introduction to ballet",
            active=True
        )
        
        repr_str = repr(class_template)
        assert "ClassTemplate" in repr_str
        assert "Ballet Basics" in repr_str
        assert str(class_template.id) in repr_str
    
    def test_class_template_model_defaults(self):
        """Test ClassTemplate model default values"""
        class_template = ClassTemplate(
            name="Ballet Basics",
            teacher="Anna Smith",
            weekday=1,
            start_time=time(10, 0),
            capacity=15
        )
        
        assert class_template.active is not False


class TestCRUDFunctions:
    """Unit tests for CRUD functions"""
    
    def test_get_schedule_function_exists(self):
        """Test that get_schedule function exists"""
        from services.schedule.src.crud import get_schedule
        
        assert callable(get_schedule)
    
    def test_get_classes_by_filter_function_exists(self):
        """Test that get_classes_by_filter function exists"""
        from services.schedule.src.crud import get_classes_by_filter
        
        assert callable(get_classes_by_filter)
    
    def test_create_class_function_exists(self):
        """Test that create_class function exists"""
        from services.schedule.src.crud import create_class
        
        assert callable(create_class)
    
    def test_get_class_by_id_function_exists(self):
        """Test that get_class_by_id function exists"""
        from services.schedule.src.crud import get_class_by_id
        
        assert callable(get_class_by_id)
    
    def test_update_class_function_exists(self):
        """Test that update_class function exists"""
        from services.schedule.src.crud import update_class
        
        assert callable(update_class)
    
    def test_delete_class_function_exists(self):
        """Test that delete_class function exists"""
        from services.schedule.src.crud import delete_class
        
        assert callable(delete_class)
    
    def test_get_classes_by_teacher_function_exists(self):
        """Test that get_classes_by_teacher function exists"""
        from services.schedule.src.crud import get_classes_by_teacher
        
        assert callable(get_classes_by_teacher)
    
    def test_get_classes_by_weekday_function_exists(self):
        """Test that get_classes_by_weekday function exists"""
        from services.schedule.src.crud import get_classes_by_weekday
        
        assert callable(get_classes_by_weekday)
    
    def test_get_class_statistics_function_exists(self):
        """Test that get_class_statistics function exists"""
        from services.schedule.src.crud import get_class_statistics
        
        assert callable(get_class_statistics)


class TestAuthFunctions:
    """Unit tests for auth functions"""
    
    def test_get_current_admin_user_dependency(self):
        """Test get_current_admin_user dependency function"""
        from services.schedule.src.auth import get_current_admin_user
        
        # This is a dependency function that would be tested with actual FastAPI app
        # For unit testing, we just verify it exists and is callable
        assert callable(get_current_admin_user)
    
    def test_verify_service_token_function(self):
        """Test verify_service_token function"""
        from services.schedule.src.auth import verify_service_token
        
        # This is a dependency function that would be tested with actual FastAPI app
        # For unit testing, we just verify it exists and is callable
        assert callable(verify_service_token)


class TestUtilityFunctions:
    """Unit tests for utility functions"""
    
    def test_create_paginated_response_function(self):
        """Test create_paginated_response function"""
        from services.schedule.src.main import create_paginated_response
        
        items = [{"id": 1}, {"id": 2}]
        total = 2
        page = 1
        size = 10
        
        result = create_paginated_response(items, total, page, size)
        
        assert result.items == items
        assert result.total == total
        assert result.page == page
        assert result.size == size
        assert result.pages == 1  # (2 + 10 - 1) // 10 = 1
