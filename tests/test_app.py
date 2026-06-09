"""
Test suite for Mergington High School Activities API

Tests cover:
- Fetching all activities
- Signing up for activities
- Unregistering from activities
- Error handling and validation
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    initial_state = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
    }
    activities.clear()
    activities.update(initial_state)
    yield
    activities.clear()
    activities.update(initial_state)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Should return all activities with correct structure"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        assert "Chess Club" in data
        assert "Programming Class" in data
    
    def test_activity_has_required_fields(self, client, reset_activities):
        """Should include all required fields for each activity"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)
    
    def test_participants_list_is_included(self, client, reset_activities):
        """Should include participants in the response"""
        response = client.get("/activities")
        data = response.json()
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]


class TestRootRedirect:
    """Tests for GET / endpoint"""
    
    def test_root_redirects_to_static_index(self, client):
        """Root endpoint should redirect to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_successful_signup(self, client, reset_activities):
        """Should add participant to activity"""
        initial_count = len(activities["Chess Club"]["participants"])
        
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Signed up newstudent@mergington.edu for Chess Club"
        assert len(activities["Chess Club"]["participants"]) == initial_count + 1
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]
    
    def test_signup_duplicate_participant(self, client, reset_activities):
        """Should reject duplicate signup"""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Should return 404 for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_increments_participant_count(self, client, reset_activities):
        """Should correctly update participant count"""
        initial_count = len(activities["Programming Class"]["participants"])
        
        client.post(
            "/activities/Programming Class/signup?email=test1@mergington.edu"
        )
        client.post(
            "/activities/Programming Class/signup?email=test2@mergington.edu"
        )
        
        assert len(activities["Programming Class"]["participants"]) == initial_count + 2


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_successful_unregister(self, client, reset_activities):
        """Should remove participant from activity"""
        initial_count = len(activities["Chess Club"]["participants"])
        
        response = client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Unregistered michael@mergington.edu from Chess Club"
        assert len(activities["Chess Club"]["participants"]) == initial_count - 1
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_participant(self, client, reset_activities):
        """Should reject unregister of non-existent participant"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=notparticipant@mergington.edu"
        )
        
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_unregister_from_nonexistent_activity(self, client, reset_activities):
        """Should return 404 for non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent Club/unregister?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_unregister_decrements_participant_count(self, client, reset_activities):
        """Should correctly decrease participant count"""
        initial_count = len(activities["Chess Club"]["participants"])
        
        client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        client.delete(
            "/activities/Chess Club/unregister?email=daniel@mergington.edu"
        )
        
        assert len(activities["Chess Club"]["participants"]) == initial_count - 2


class TestSignupAndUnregisterFlow:
    """Integration tests for signup and unregister flow"""
    
    def test_signup_then_unregister(self, client, reset_activities):
        """Should handle signup followed by unregister"""
        email = "tempstudent@mergington.edu"
        
        # Signup
        signup_response = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert signup_response.status_code == 200
        assert email in activities["Chess Club"]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/Chess Club/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        assert email not in activities["Chess Club"]["participants"]
    
    def test_signup_unregister_signup_again(self, client, reset_activities):
        """Should allow signup after unregister"""
        email = "tempstudent@mergington.edu"
        
        # First signup
        client.post(f"/activities/Chess Club/signup?email={email}")
        assert email in activities["Chess Club"]["participants"]
        
        # Unregister
        client.delete(f"/activities/Chess Club/unregister?email={email}")
        assert email not in activities["Chess Club"]["participants"]
        
        # Signup again
        response = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response.status_code == 200
        assert email in activities["Chess Club"]["participants"]
