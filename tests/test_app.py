"""
Test suite for FastAPI activities application using AAA (Arrange-Act-Assert) pattern.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """
    Arrange: Create a test client for the FastAPI app.
    This fixture is used in all tests.
    """
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """
    Arrange: Reset activities to initial state before each test.
    """
    from src.app import activities
    
    # Store original state
    original_activities = {
        name: {
            "description": activity["description"],
            "schedule": activity["schedule"],
            "max_participants": activity["max_participants"],
            "participants": activity["participants"].copy()
        }
        for name, activity in activities.items()
    }
    
    yield
    
    # Restore original state after test
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_all_activities_returns_200(self, client):
        """
        Arrange: Test client ready
        Act: GET /activities
        Assert: Response status is 200 and returns activities
        """
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        activities_data = response.json()
        assert isinstance(activities_data, dict)
        assert len(activities_data) > 0
    
    def test_get_activities_includes_required_fields(self, client):
        """
        Arrange: Test client ready
        Act: GET /activities
        Assert: Each activity has required fields
        """
        # Act
        response = client.get("/activities")
        activities_data = response.json()
        
        # Assert
        for activity_name, activity in activities_data.items():
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity
            assert isinstance(activity["participants"], list)
    
    def test_get_activities_has_specific_activities(self, client):
        """
        Arrange: Test client ready
        Act: GET /activities
        Assert: Expected activities are present
        """
        # Act
        response = client.get("/activities")
        activities_data = response.json()
        
        # Assert
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]
        for activity in expected_activities:
            assert activity in activities_data


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_student_returns_200(self, client, reset_activities):
        """
        Arrange: Prepare signup request for unassigned student
        Act: POST signup endpoint
        Assert: Response is 200 and student added to participants
        """
        # Arrange
        activity_name = "Chess Club"
        email = "newtesting@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
    
    def test_signup_duplicate_email_returns_400(self, client, reset_activities):
        """
        Arrange: Try to signup with email already in activity
        Act: POST signup with duplicate email
        Assert: Response is 400 with appropriate error
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in Chess Club
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()
    
    def test_signup_nonexistent_activity_returns_404(self, client):
        """
        Arrange: Prepare signup for activity that doesn't exist
        Act: POST signup with invalid activity name
        Assert: Response is 404 with not found error
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_adds_participant_to_list(self, client, reset_activities):
        """
        Arrange: Get initial participant count
        Act: Signup new student
        Assert: Participant count increases and email is in list
        """
        # Arrange
        activity_name = "Gym Class"
        email = "newstudent@mergington.edu"
        get_response = client.get("/activities")
        initial_count = len(get_response.json()[activity_name]["participants"])
        
        # Act
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        get_response = client.get("/activities")
        updated_activity = get_response.json()[activity_name]
        assert len(updated_activity["participants"]) == initial_count + 1
        assert email in updated_activity["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""
    
    def test_unregister_existing_student_returns_200(self, client, reset_activities):
        """
        Arrange: Prepare delete request for registered student
        Act: DELETE signup endpoint
        Assert: Response is 200 and student removed from participants
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in Chess Club
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
    
    def test_unregister_nonexistent_student_returns_400(self, client, reset_activities):
        """
        Arrange: Try to unregister student not signed up
        Act: DELETE with invalid email
        Assert: Response is 400 with not signed up error
        """
        # Arrange
        activity_name = "Chess Club"
        email = "notstudent@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()
    
    def test_unregister_nonexistent_activity_returns_404(self, client):
        """
        Arrange: Prepare delete request for activity that doesn't exist
        Act: DELETE from invalid activity
        Assert: Response is 404 with not found error
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_unregister_removes_participant_from_list(self, client, reset_activities):
        """
        Arrange: Get initial participant count with known email
        Act: Unregister student
        Assert: Participant count decreases and email is removed
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        get_response = client.get("/activities")
        initial_count = len(get_response.json()[activity_name]["participants"])
        
        # Act
        client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        get_response = client.get("/activities")
        updated_activity = get_response.json()[activity_name]
        assert len(updated_activity["participants"]) == initial_count - 1
        assert email not in updated_activity["participants"]


class TestRootRedirect:
    """Tests for GET / endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """
        Arrange: Test client ready
        Act: GET /
        Assert: Response redirects to /static/index.html
        """
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
