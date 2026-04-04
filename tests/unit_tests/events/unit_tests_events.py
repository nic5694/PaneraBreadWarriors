import pytest
import json
from unittest.mock import MagicMock, patch
from app.services.event_service import EventService, UrlNotFoundError

# 1. Test successful event creation logic
@patch('app.models.events.Event.create')
@patch('app.models.urls.Url.get_by_id')
def test_create_event_success(mock_url_get, mock_event_create):
    # Arrange
    service = EventService()
    
    # Simulate Url.get_by_id succeeding
    mock_url_get.return_value = MagicMock(id=123) 
    
    # Simulate Event.create returning an object with an ID
    # Note: If your Service returns a dict, we change the assert below
    mock_event_create.return_value = MagicMock(id=1)
    
    data = {
        "url_id": "test-link",
        "event_type": "click",
        "details": {"ip": "1.1.1.1"}
    }

    # Act
    result = service.create_event(data)

    # Assert
    # If your service returns a DICT (which the error suggests), use:
    assert result['id'] == 1 
    # If it returns an OBJECT, use: result.id == 1
    mock_event_create.assert_called_once()

# 2. Test failure when URL doesn't exist
@patch('app.models.urls.Url.get_by_id')
def test_create_event_url_not_found(mock_url_get):
    from app.models.urls import Url # Import here to avoid proxy issues early
    service = EventService()
    
    # Simulate the Peewee DoesNotExist exception
    mock_url_get.side_effect = Url.DoesNotExist
    
    with pytest.raises(UrlNotFoundError):
        service.create_event({"url_id": "fake", "event_type": "view"})

# 3. Test validation
def test_create_event_missing_required_fields():
    service = EventService()
    
    # Testing that the service enforces required fields
    with pytest.raises(ValueError) as exc:
        service.create_event({"url_id": "test-only"}) # Missing event_type
        
    assert "url_id and event_type are required" in str(exc.value)