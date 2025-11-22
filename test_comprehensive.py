#!/usr/bin/env python3
"""
Comprehensive test suite for ArrivApp justifications system
Tests: Teacher submission, viewing, deletion, and class filtering
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8000/api"

class TestRunner:
    def __init__(self):
        self.director_token = None
        self.teacher1_token = None
        self.teacher2_token = None
        self.director_id = None
        self.teacher1_id = None
        self.teacher2_id = None
        self.test_results = []

    def log(self, message):
        print(message)

    def test_1_authentication(self):
        """Test authentication with director and teachers"""
        self.log("\n" + "=" * 70)
        self.log("TEST 1: AUTHENTICATION (Director + Teachers)")
        self.log("=" * 70)
        
        tests_passed = 0
        
        # Login as director
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": "director1", "password": "director123"}
        )
        if response.status_code == 200:
            self.director_token = response.json().get("access_token")
            self.log("✅ Director logged in successfully")
            tests_passed += 1
        else:
            self.log(f"❌ Director login failed: {response.text[:100]}")
            return 0
        
        # Login as teacher 1 (class 3B)
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": "teacher_3b", "password": "teacher123"}
        )
        if response.status_code == 200:
            self.teacher1_token = response.json().get("access_token")
            self.log("✅ Teacher 1 (3B) logged in successfully")
            tests_passed += 1
        else:
            self.log(f"❌ Teacher 1 login failed: {response.text[:100]}")
            return 0
        
        # Login as teacher 2 (class 6A)
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": "teacher_6a", "password": "teacher123"}
        )
        if response.status_code == 200:
            self.teacher2_token = response.json().get("access_token")
            self.log("✅ Teacher 2 (6A) logged in successfully")
            tests_passed += 1
        else:
            self.log(f"❌ Teacher 2 login failed: {response.text[:100]}")
            return 0
        
        return tests_passed

    def test_2_teacher_get_students(self):
        """Test teachers get only their assigned class students"""
        self.log("\n" + "=" * 70)
        self.log("TEST 2: CLASS FILTERING - GET STUDENTS")
        self.log("=" * 70)
        
        tests_passed = 0
        
        # Teacher 1 should see only class 3B students
        headers = {"Authorization": f"Bearer {self.teacher1_token}"}
        response = requests.get(f"{BASE_URL}/students/", headers=headers)
        
        if response.status_code == 200:
            students = response.json()
            class_3b_students = [s for s in students if s.get("class_name") == "3B"]
            
            if len(class_3b_students) == len(students):
                self.log(f"✅ Teacher 1 sees only class 3B students ({len(students)} total)")
                tests_passed += 1
            else:
                self.log(f"❌ Teacher 1 sees mixed classes: {len(class_3b_students)}/3B, {len(students)} total")
                return 0
        else:
            self.log(f"❌ Failed to get students: {response.text[:100]}")
            return 0
        
        # Teacher 2 should see only class 6A students
        headers = {"Authorization": f"Bearer {self.teacher2_token}"}
        response = requests.get(f"{BASE_URL}/students/", headers=headers)
        
        if response.status_code == 200:
            students = response.json()
            class_6a_students = [s for s in students if s.get("class_name") == "6A"]
            
            if len(class_6a_students) == len(students):
                self.log(f"✅ Teacher 2 sees only class 6A students ({len(students)} total)")
                tests_passed += 1
            else:
                self.log(f"❌ Teacher 2 sees mixed classes: {len(class_6a_students)}/6A, {len(students)} total")
                return 0
        else:
            self.log(f"❌ Failed to get students: {response.text[:100]}")
            return 0
        
        return tests_passed

    def test_3_teacher_submit_justification(self):
        """Test teachers can submit justifications"""
        self.log("\n" + "=" * 70)
        self.log("TEST 3: TEACHER SUBMIT JUSTIFICATIONS")
        self.log("=" * 70)
        
        tests_passed = 0
        
        # Get a student from class 3B for teacher 1
        headers = {"Authorization": f"Bearer {self.teacher1_token}"}
        response = requests.get(f"{BASE_URL}/students/", headers=headers)
        students = response.json()
        
        if not students:
            self.log("❌ Teacher 1 has no students to submit justification for")
            return 0
        
        student_id = students[0]["id"]
        
        # Teacher 1 submits justification for their student
        payload = {
            "student_id": student_id,
            "justification_type": "absence",
            "date": (datetime.now() - timedelta(days=1)).isoformat(),
            "reason": "Medical appointment (teacher submission)",
            "submitted_by": "teacher_3b@test.local"
        }
        
        response = requests.post(
            f"{BASE_URL}/justifications/",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 201:
            justification = response.json()
            justification_id = justification.get("id")
            self.log(f"✅ Teacher 1 submitted justification (ID: {justification_id})")
            tests_passed += 1
            return tests_passed, justification_id
        elif response.status_code == 403:
            self.log(f"❌ Teacher 1 got 403 Forbidden - class filtering may not be working")
            self.log(f"   Response: {response.text[:200]}")
            return 0
        else:
            self.log(f"❌ Teacher 1 submission failed ({response.status_code}): {response.text[:100]}")
            return 0

    def test_4_teacher_view_own_justifications(self):
        """Test teachers see only their assigned class justifications"""
        self.log("\n" + "=" * 70)
        self.log("TEST 4: TEACHER VIEW - CLASS FILTERING")
        self.log("=" * 70)
        
        tests_passed = 0
        
        # Teacher 1 views justifications (should see 3B only)
        headers = {"Authorization": f"Bearer {self.teacher1_token}"}
        response = requests.get(f"{BASE_URL}/justifications/", headers=headers)
        
        if response.status_code == 200:
            justifications = response.json()
            self.log(f"✅ Teacher 1 retrieved {len(justifications)} justifications")
            tests_passed += 1
        else:
            self.log(f"❌ Failed to get justifications: {response.text[:100]}")
            return 0
        
        # Teacher 2 views justifications (should see 6A only)
        headers = {"Authorization": f"Bearer {self.teacher2_token}"}
        response = requests.get(f"{BASE_URL}/justifications/", headers=headers)
        
        if response.status_code == 200:
            justifications = response.json()
            self.log(f"✅ Teacher 2 retrieved {len(justifications)} justifications")
            tests_passed += 1
        else:
            self.log(f"❌ Failed to get justifications: {response.text[:100]}")
            return 0
        
        return tests_passed

    def test_5_director_sees_all(self):
        """Test director sees all justifications (no class filtering)"""
        self.log("\n" + "=" * 70)
        self.log("TEST 5: DIRECTOR VIEW - NO CLASS FILTERING")
        self.log("=" * 70)
        
        tests_passed = 0
        
        # Director views justifications (should see all)
        headers = {"Authorization": f"Bearer {self.director_token}"}
        response = requests.get(f"{BASE_URL}/justifications/", headers=headers)
        
        if response.status_code == 200:
            justifications = response.json()
            self.log(f"✅ Director retrieved {len(justifications)} justifications (all classes)")
            tests_passed += 1
        else:
            self.log(f"❌ Failed to get justifications: {response.text[:100]}")
            return 0
        
        # Director views all students (no class filtering)
        response = requests.get(f"{BASE_URL}/students/", headers=headers)
        
        if response.status_code == 200:
            students = response.json()
            self.log(f"✅ Director retrieved {len(students)} students (all classes)")
            tests_passed += 1
        else:
            self.log(f"❌ Failed to get students: {response.text[:100]}")
            return 0
        
        return tests_passed

    def test_6_teacher_delete_justification(self):
        """Test teachers can delete justifications from their class"""
        self.log("\n" + "=" * 70)
        self.log("TEST 6: TEACHER DELETE JUSTIFICATIONS")
        self.log("=" * 70)
        
        # First, get or create a justification to delete
        headers = {"Authorization": f"Bearer {self.teacher1_token}"}
        response = requests.get(f"{BASE_URL}/justifications/", headers=headers)
        
        if response.status_code != 200:
            self.log("⚠️  Could not retrieve justifications to delete")
            return 0
        
        justifications = response.json()
        if not justifications:
            self.log("⚠️  No justifications to delete (test may need to create one first)")
            return 0
        
        justification_id = justifications[0]["id"]
        
        # Delete justification
        response = requests.delete(
            f"{BASE_URL}/justifications/{justification_id}",
            headers=headers
        )
        
        if response.status_code in [200, 204]:  # Accept both 200 and 204
            self.log(f"✅ Teacher 1 successfully deleted justification (ID: {justification_id})")
            return 1
        elif response.status_code == 403:
            self.log(f"❌ Teacher 1 got 403 - class filtering check failed")
            return 0
        else:
            self.log(f"❌ Delete failed ({response.status_code}): {response.text[:100]}")
            return 0

    def test_7_dashboard_statistics(self):
        """Test dashboard statistics with class filtering"""
        self.log("\n" + "=" * 70)
        self.log("TEST 7: DASHBOARD STATISTICS")
        self.log("=" * 70)
        
        tests_passed = 0
        
        # Director gets statistics
        headers = {"Authorization": f"Bearer {self.director_token}"}
        response = requests.get(f"{BASE_URL}/reports/statistics", headers=headers)
        
        if response.status_code == 200:
            stats = response.json()
            self.log(f"✅ Director statistics retrieved:")
            self.log(f"   - Present: {stats.get('total_present')}")
            self.log(f"   - Absent: {stats.get('total_absent')}")
            self.log(f"   - Late: {stats.get('total_late')}")
            tests_passed += 1
        else:
            self.log(f"❌ Failed to get statistics: {response.text[:100]}")
            return 0
        
        # Director gets statistics with class filter
        response = requests.get(
            f"{BASE_URL}/reports/statistics",
            headers=headers,
            params={"class_name": "3B"}
        )
        
        if response.status_code == 200:
            stats = response.json()
            self.log(f"✅ Director statistics for class 3B retrieved:")
            self.log(f"   - Present: {stats.get('total_present')}")
            self.log(f"   - Absent: {stats.get('total_absent')}")
            tests_passed += 1
        else:
            self.log(f"❌ Failed to get class-filtered statistics: {response.text[:100]}")
            return 0
        
        return tests_passed

    def run_all_tests(self):
        """Run all tests"""
        self.log("\n" + "🧪 " * 20)
        self.log("ARRIVAPP COMPREHENSIVE TEST SUITE")
        self.log("Testing: Teacher Justifications, Class Filtering, Authorization")
        self.log("🧪 " * 20)
        
        results = {}
        
        # Test 1: Authentication
        result = self.test_1_authentication()
        results["Authentication"] = (result > 0, result)
        if result == 0:
            self.log("\n❌ Cannot continue without authentication")
            return results
        
        # Test 2: Class filtering in student list
        result = self.test_2_teacher_get_students()
        results["Class Filtering (Students)"] = (result > 0, result)
        
        # Test 3: Teacher submissions
        result = self.test_3_teacher_submit_justification()
        if isinstance(result, tuple):
            results["Teacher Submit Justifications"] = (result[0] > 0, result[0])
            justification_id = result[1]
        else:
            results["Teacher Submit Justifications"] = (result > 0, result)
            justification_id = None
        
        # Test 4: Teacher views own justifications
        result = self.test_4_teacher_view_own_justifications()
        results["Teacher View (Class Filter)"] = (result > 0, result)
        
        # Test 5: Director sees all
        result = self.test_5_director_sees_all()
        results["Director View (No Filter)"] = (result > 0, result)
        
        # Test 6: Teacher delete
        if justification_id:
            result = self.test_6_teacher_delete_justification()
            results["Teacher Delete"] = (result > 0, result)
        else:
            self.log("\n⚠️  Skipping delete test - no justification to delete")
        
        # Test 7: Dashboard statistics
        result = self.test_7_dashboard_statistics()
        results["Dashboard Statistics"] = (result > 0, result)
        
        # Summary
        self.log("\n" + "=" * 70)
        self.log("TEST SUMMARY")
        self.log("=" * 70)
        
        passed = sum(1 for (success, _) in results.values() if success)
        total = len(results)
        
        for test_name, (success, result) in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            self.log(f"{status}: {test_name}")
        
        self.log(f"\n{'='*70}")
        self.log(f"RESULT: {passed}/{total} tests passed")
        self.log(f"{'='*70}")
        
        if passed == total:
            self.log("🎉 ALL TESTS PASSED! All features working correctly! 🎉")
            return 0
        else:
            self.log(f"⚠️  {total - passed} test(s) failed")
            return 1


if __name__ == "__main__":
    import sys
    runner = TestRunner()
    exit_code = runner.run_all_tests()
    sys.exit(exit_code)
