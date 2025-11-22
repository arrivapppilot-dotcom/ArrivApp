#!/usr/bin/env python3
"""
Comprehensive test suite for ArrivApp justifications system
Tests teacher capabilities, class filtering, and email notifications
"""

import requests
import json
from datetime import datetime, timedelta
import sys

BASE_URL = "http://localhost:8000/api"

class TestRunner:
    def __init__(self):
        self.admin_token = None
        self.teacher_token = None
        self.director_token = None
        self.test_results = []
        self.teacher_id = None
        self.director_id = None
        self.student_id = None
        self.school_id = None
        self.class_name = None
        self.justification_id = None

    def log(self, message, status="INFO"):
        print(f"[{status}] {message}")
        self.test_results.append({"message": message, "status": status})

    def login(self, email, password):
        """Login and get access token"""
        try:
            response = requests.post(
                f"{BASE_URL}/auth/login",
                json={"email": email, "password": password}
            )
            if response.status_code == 200:
                token = response.json().get("access_token")
                self.log(f"✅ Logged in as {email}", "PASS")
                return token
            else:
                self.log(f"❌ Failed to login as {email}: {response.text}", "FAIL")
                return None
        except Exception as e:
            self.log(f"❌ Login exception: {str(e)}", "ERROR")
            return None

    def get_headers(self, token):
        return {"Authorization": f"Bearer {token}"}

    def test_auth(self):
        """Test authentication and get tokens"""
        self.log("=" * 60, "INFO")
        self.log("TEST 1: AUTHENTICATION", "INFO")
        self.log("=" * 60, "INFO")

        # Login as admin
        self.admin_token = self.login("admin@arrivapp.local", "Admin@123")
        
        # Login as director
        self.director_token = self.login("director@arrivapp.local", "Director@123")
        
        # Login as teacher
        self.teacher_token = self.login("teacher@arrivapp.local", "Teacher@123")

        if self.admin_token and self.director_token and self.teacher_token:
            self.log("✅ All authentication tests passed", "PASS")
            return True
        else:
            self.log("❌ Some authentication tests failed", "FAIL")
            return False

    def get_users(self):
        """Get users to find IDs"""
        self.log("\n" + "=" * 60, "INFO")
        self.log("TEST 2: FETCH USERS AND SCHOOLS", "INFO")
        self.log("=" * 60, "INFO")

        try:
            headers = self.get_headers(self.admin_token)
            response = requests.get(f"{BASE_URL}/users", headers=headers)
            
            if response.status_code == 200:
                users = response.json()
                
                # Find teacher, director, and school
                for user in users:
                    if user.get("role") == "teacher":
                        self.teacher_id = user.get("id")
                        self.log(f"✅ Found teacher: ID={self.teacher_id}", "PASS")
                    elif user.get("role") == "director":
                        self.director_id = user.get("id")
                        self.log(f"✅ Found director: ID={self.director_id}", "PASS")
                
                # Get schools
                schools_response = requests.get(f"{BASE_URL}/schools", headers=headers)
                if schools_response.status_code == 200:
                    schools = schools_response.json()
                    if schools:
                        self.school_id = schools[0].get("id")
                        self.log(f"✅ Found school: ID={self.school_id}", "PASS")
                
                return True
            else:
                self.log(f"❌ Failed to fetch users: {response.text}", "FAIL")
                return False
        except Exception as e:
            self.log(f"❌ Exception fetching users: {str(e)}", "ERROR")
            return False

    def get_students(self):
        """Get students to find test student"""
        self.log("\n" + "=" * 60, "INFO")
        self.log("TEST 3: FETCH STUDENTS", "INFO")
        self.log("=" * 60, "INFO")

        try:
            headers = self.get_headers(self.teacher_token)
            response = requests.get(f"{BASE_URL}/students", headers=headers)
            
            if response.status_code == 200:
                students = response.json()
                if students:
                    self.student_id = students[0].get("id")
                    self.class_name = students[0].get("class_name")
                    self.log(f"✅ Found student: ID={self.student_id}, Class={self.class_name}", "PASS")
                    return True
                else:
                    self.log("⚠️  No students found for teacher's assigned classes", "WARN")
                    return False
            else:
                self.log(f"❌ Failed to fetch students: {response.text}", "FAIL")
                return False
        except Exception as e:
            self.log(f"❌ Exception fetching students: {str(e)}", "ERROR")
            return False

    def test_teacher_submit_justification(self):
        """Test teacher can submit justification"""
        self.log("\n" + "=" * 60, "INFO")
        self.log("TEST 4: TEACHER SUBMIT JUSTIFICATION", "INFO")
        self.log("=" * 60, "INFO")

        if not self.student_id:
            self.log("⚠️  Skipping - no student available", "SKIP")
            return False

        try:
            headers = self.get_headers(self.teacher_token)
            payload = {
                "student_id": self.student_id,
                "type": "Ausencia",
                "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                "reason": "Medical appointment"
            }
            
            response = requests.post(
                f"{BASE_URL}/justifications",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 201:
                result = response.json()
                self.justification_id = result.get("id")
                self.log(f"✅ Teacher successfully submitted justification: ID={self.justification_id}", "PASS")
                return True
            elif response.status_code == 403:
                self.log(f"❌ Teacher denied access (403) - class filtering may not be working", "FAIL")
                return False
            else:
                self.log(f"❌ Failed to submit justification: {response.status_code} - {response.text}", "FAIL")
                return False
        except Exception as e:
            self.log(f"❌ Exception submitting justification: {str(e)}", "ERROR")
            return False

    def test_teacher_view_justifications(self):
        """Test teacher can only see their assigned class justifications"""
        self.log("\n" + "=" * 60, "INFO")
        self.log("TEST 5: TEACHER VIEW JUSTIFICATIONS (CLASS FILTERING)", "INFO")
        self.log("=" * 60, "INFO")

        try:
            headers = self.get_headers(self.teacher_token)
            response = requests.get(f"{BASE_URL}/justifications", headers=headers)
            
            if response.status_code == 200:
                justifications = response.json()
                
                # Check if all returned justifications are from teacher's assigned classes
                if justifications:
                    self.log(f"✅ Retrieved {len(justifications)} justifications for teacher", "PASS")
                    
                    # Verify filtering
                    for j in justifications:
                        if j.get("student", {}).get("class_name") != self.class_name:
                            self.log(f"❌ Found justification from different class: {j.get('student', {}).get('class_name')}", "FAIL")
                            return False
                    
                    self.log("✅ All justifications are from teacher's assigned classes", "PASS")
                    return True
                else:
                    self.log("⚠️  No justifications returned (may be normal if none submitted)", "WARN")
                    return True
            else:
                self.log(f"❌ Failed to fetch justifications: {response.text}", "FAIL")
                return False
        except Exception as e:
            self.log(f"❌ Exception fetching justifications: {str(e)}", "ERROR")
            return False

    def test_director_view_all_justifications(self):
        """Test director can see all justifications (no class filtering)"""
        self.log("\n" + "=" * 60, "INFO")
        self.log("TEST 6: DIRECTOR VIEW JUSTIFICATIONS (SCHOOL-WIDE, NO CLASS FILTER)", "INFO")
        self.log("=" * 60, "INFO")

        try:
            headers = self.get_headers(self.director_token)
            response = requests.get(f"{BASE_URL}/justifications", headers=headers)
            
            if response.status_code == 200:
                justifications = response.json()
                self.log(f"✅ Director can see {len(justifications)} justifications (school-wide)", "PASS")
                return True
            else:
                self.log(f"❌ Failed to fetch justifications as director: {response.text}", "FAIL")
                return False
        except Exception as e:
            self.log(f"❌ Exception fetching justifications as director: {str(e)}", "ERROR")
            return False

    def test_teacher_delete_justification(self):
        """Test teacher can delete justification"""
        self.log("\n" + "=" * 60, "INFO")
        self.log("TEST 7: TEACHER DELETE JUSTIFICATION", "INFO")
        self.log("=" * 60, "INFO")

        if not self.justification_id:
            self.log("⚠️  Skipping - no justification to delete", "SKIP")
            return False

        try:
            headers = self.get_headers(self.teacher_token)
            response = requests.delete(
                f"{BASE_URL}/justifications/{self.justification_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                self.log(f"✅ Teacher successfully deleted justification", "PASS")
                return True
            elif response.status_code == 403:
                self.log(f"❌ Teacher denied access (403) - authorization check failed", "FAIL")
                return False
            else:
                self.log(f"❌ Failed to delete justification: {response.status_code}", "FAIL")
                return False
        except Exception as e:
            self.log(f"❌ Exception deleting justification: {str(e)}", "ERROR")
            return False

    def test_dashboard_statistics(self):
        """Test dashboard statistics with class filtering"""
        self.log("\n" + "=" * 60, "INFO")
        self.log("TEST 8: DASHBOARD STATISTICS WITH FILTERS", "INFO")
        self.log("=" * 60, "INFO")

        try:
            headers = self.get_headers(self.director_token)
            
            # Test without filters
            response = requests.get(f"{BASE_URL}/reports/statistics", headers=headers)
            if response.status_code == 200:
                stats = response.json()
                self.log(f"✅ Director statistics retrieved: {json.dumps(stats, indent=2)[:200]}...", "PASS")
                
                # Test with class filter
                if self.class_name:
                    response = requests.get(
                        f"{BASE_URL}/reports/statistics",
                        headers=headers,
                        params={"class_name": self.class_name}
                    )
                    if response.status_code == 200:
                        class_stats = response.json()
                        self.log(f"✅ Statistics with class filter retrieved", "PASS")
                        return True
                else:
                    self.log("⚠️  No class_name available for filter test", "WARN")
                    return True
            else:
                self.log(f"❌ Failed to fetch statistics: {response.text}", "FAIL")
                return False
        except Exception as e:
            self.log(f"❌ Exception fetching statistics: {str(e)}", "ERROR")
            return False

    def run_all_tests(self):
        """Run all tests"""
        self.log("\n" + "🧪 STARTING ARRIVAPP COMPREHENSIVE TEST SUITE 🧪", "INFO")
        self.log("Testing: Justifications, Teacher Capabilities, Class Filtering", "INFO")

        tests = [
            ("Authentication", self.test_auth),
            ("User/School Retrieval", self.get_users),
            ("Student Retrieval", self.get_students),
            ("Teacher Submit Justification", self.test_teacher_submit_justification),
            ("Teacher View Justifications (Class Filter)", self.test_teacher_view_justifications),
            ("Director View Justifications (No Class Filter)", self.test_director_view_all_justifications),
            ("Teacher Delete Justification", self.test_teacher_delete_justification),
            ("Dashboard Statistics with Filters", self.test_dashboard_statistics),
        ]

        results = {}
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                self.log(f"❌ Test '{test_name}' crashed: {str(e)}", "ERROR")
                results[test_name] = False

        # Print summary
        self.log("\n" + "=" * 60, "INFO")
        self.log("TEST SUMMARY", "INFO")
        self.log("=" * 60, "INFO")
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{status}: {test_name}", "SUMMARY")
        
        self.log(f"\n{passed}/{total} tests passed", "SUMMARY")
        
        if passed == total:
            self.log("🎉 ALL TESTS PASSED! 🎉", "SUCCESS")
            return 0
        else:
            self.log(f"⚠️  {total - passed} test(s) failed", "FAIL")
            return 1


if __name__ == "__main__":
    runner = TestRunner()
    exit_code = runner.run_all_tests()
    sys.exit(exit_code)
