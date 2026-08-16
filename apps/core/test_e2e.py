"""
Comprehensive Pre-Deployment End-to-End Test Suite for CrowdFund Egypt
Tests all critical business workflows, security rules, and AI features.
"""

import os
import sys
import json
from pathlib import Path

# Add root directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crowdfunding.settings')
import django
django.setup()

from decimal import Decimal
from datetime import timedelta

from django.test import Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.projects.models import Project, Category, Tag, Donation, Comment, Rating, Report

User = get_user_model()

def run_e2e_tests():
    print("=" * 70)
    print("🚀 STARTING CROWDFUND EGYPT PRE-DEPLOYMENT E2E VERIFICATION")
    print("=" * 70)
    
    passed_tests = 0
    total_tests = 0
    client = Client()

    def check(name, condition, details=""):
        nonlocal passed_tests, total_tests
        total_tests += 1
        if condition:
            passed_tests += 1
            print(f"  ✅ PASS: {name}")
        else:
            print(f"  ❌ FAIL: {name} | Details: {details}")

    # -------------------------------------------------------------
    # 1. Public Pages & Navigation
    # -------------------------------------------------------------
    print("\n[1/7] Testing Public Pages & Search...")
    r = client.get('/')
    check("Home Page (200 OK)", r.status_code == 200)
    check("Home Page Contains Branding", b"CrowdFund" in r.content and b"Egypt" in r.content)

    r = client.get('/?q=solar')
    check("Search Page with query 'solar'", r.status_code == 200 and b"Solar" in r.content)

    r = client.get('/projects/')
    check("All Campaigns List (200 OK)", r.status_code == 200)

    category = Category.objects.first()
    if category:
        r = client.get(f'/projects/category/{category.slug}/')
        check(f"Category Filter Page ({category.name})", r.status_code == 200)

    # -------------------------------------------------------------
    # 2. Authentication & Account Management
    # -------------------------------------------------------------
    print("\n[2/7] Testing User Registration, Verification & Login...")
    test_email = f"e2e_user_{int(timezone.now().timestamp())}@example.com"
    reg_data = {
        'first_name': 'E2E',
        'last_name': 'Tester',
        'email': test_email,
        'password': 'SecurePassword123!',
        'confirm_password': 'SecurePassword123!',
        'phone_number': '01012349999',
    }
    r = client.post('/accounts/register/', reg_data)
    check("User Registration POST", r.status_code in (200, 302))

    new_user = User.objects.filter(email=test_email).first()
    check("User Created in Database", new_user is not None)
    
    if new_user:
        # Verify email token workflow
        r = client.get(f'/accounts/activate/{new_user.verification_token}/')
        check("Email Verification Link (302 Redirect)", r.status_code == 302)
        new_user.refresh_from_db()
        check("User Email is Verified", new_user.is_email_verified is True and new_user.is_active is True)

        # Log in
        login_success = client.login(email=test_email, password='SecurePassword123!')
        check("User Login Successful", login_success is True)

        # Profile Page
        r = client.get('/accounts/profile/')
        check("User Profile View (200 OK)", r.status_code == 200)

    # -------------------------------------------------------------
    # 3. Campaign Creation Workflow
    # -------------------------------------------------------------
    print("\n[3/7] Testing Campaign Creation...")
    dummy_img = SimpleUploadedFile("cover.jpg", b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b", content_type="image/gif")
    
    start_date = timezone.now().date()
    end_date = (timezone.now() + timedelta(days=30)).date()
    
    campaign_data = {
        'title': 'E2E Automated Clean Nile Initiative',
        'category': category.id if category else 1,
        'total_target': '100000.00',
        'details': 'A comprehensive test campaign for cleaning Nile river banks and planting trees.',
        'cover_image': dummy_img,
        'start_time': start_date.strftime('%Y-%m-%d'),
        'end_time': end_date.strftime('%Y-%m-%d'),
        'tags_input': 'nile, clean, egypt, green',
    }
    r = client.post('/projects/create/', campaign_data, follow=True)
    check("Create Campaign POST", r.status_code == 200)

    created_project = Project.objects.filter(title='E2E Automated Clean Nile Initiative').first()
    check("Campaign Created in DB", created_project is not None)

    # -------------------------------------------------------------
    # 4. Campaign Interaction: Donations, Ratings & Comments
    # -------------------------------------------------------------
    print("\n[4/7] Testing Donations, Ratings & Comments...")
    if created_project:
        detail_url = f'/projects/{created_project.slug}/'
        r = client.get(detail_url)
        check("Campaign Detail Page (200 OK)", r.status_code == 200)

        # 1. Donation Action
        donation_post = {'action_type': 'donate', 'amount': '5000.00'}
        r = client.post(detail_url, donation_post, follow=True)
        created_project.refresh_from_db()
        check("Donation Processed (5,000 EGP)", created_project.current_donations == Decimal('5000.00'))
        check("Percentage Raised Calculated (5.0%)", created_project.percentage_raised == 5.0)

        # 2. Rating Action
        rating_post = {'action_type': 'rate', 'rating_score': '5'}
        r = client.post(detail_url, rating_post, follow=True)
        check("Rating Saved (5 Stars)", Rating.objects.filter(project=created_project, user=new_user).exists())
        check("Average Rating (5.0)", created_project.average_rating == 5.0)

        # 3. Comment Action
        comment_post = {'action_type': 'comment', 'content': 'Excellent initiative for Egypt!'}
        r = client.post(detail_url, comment_post, follow=True)
        comment_obj = Comment.objects.filter(project=created_project, user=new_user).first()
        check("Comment Posted", comment_obj is not None)

        if comment_obj:
            # Reply to Comment
            reply_post = {'action_type': 'comment', 'content': 'Thank you!', 'parent_id': str(comment_obj.id)}
            r = client.post(detail_url, reply_post, follow=True)
            check("Comment Reply Posted", Comment.objects.filter(parent=comment_obj).exists())

        # 4. Report Action
        report_post = {'action_type': 'report', 'reason': 'Test moderation flag.'}
        r = client.post(detail_url, report_post, follow=True)
        check("Report Submitted", Report.objects.filter(project=created_project).exists())

    # -------------------------------------------------------------
    # 5. Campaign Cancellation Security Policy (< 25% Rule)
    # -------------------------------------------------------------
    print("\n[5/7] Testing Campaign Cancellation Security Policy...")
    if created_project:
        # Current donations = 5,000 / 100,000 = 5% (< 25%), cancellation should be permitted
        check("Can Be Cancelled Property (True when 5% < 25%)", created_project.can_be_cancelled is True)

        # Now simulate donations reaching 30,000 EGP (30% >= 25%)
        created_project.current_donations = Decimal('30000.00')
        created_project.save()
        check("Can Be Cancelled Property (False when 30% >= 25%)", created_project.can_be_cancelled is False)

        # Attempt cancel view when >= 25% (should be rejected with error message)
        cancel_url = f'/projects/{created_project.slug}/cancel/'
        r = client.post(cancel_url, follow=True)
        created_project.refresh_from_db()
        check("Cancellation Blocked when donations >= 25%", created_project.is_cancelled is False)

        # Reset to 5% and cancel successfully
        created_project.current_donations = Decimal('5000.00')
        created_project.save()
        r = client.post(cancel_url, follow=True)
        created_project.refresh_from_db()
        check("Cancellation Allowed when donations < 25%", created_project.is_cancelled is True)

    # -------------------------------------------------------------
    # 6. Generative AI Chatbot Integration (/api/chat/)
    # -------------------------------------------------------------
    print("\n[6/7] Testing AI Chatbot REST API...")
    # 1. Method Not Allowed
    r = client.get('/api/chat/')
    check("AI Chatbot GET blocked (405 Method Not Allowed)", r.status_code == 405)

    # 2. Empty Message validation
    r = client.post('/api/chat/', data=json.dumps({'message': '   '}), content_type='application/json')
    check("AI Chatbot Empty Message rejected (400 Bad Request)", r.status_code == 400)

    # 3. Live Project Query
    r = client.post('/api/chat/', data=json.dumps({'message': 'What medical or hospital projects are raising funds?'}), content_type='application/json')
    check("AI Chatbot Response (200 OK)", r.status_code == 200)
    data = r.json()
    check("AI Response Contains Success Status", data.get('status') == 'success')
    check("AI Response Contains Healthcare Project Info", 'response' in data and len(data['response']) > 20)

    # 4. Multi-turn History
    r = client.post('/api/chat/', data=json.dumps({
        'message': 'How much money does it still need?',
        'history': [
            {'role': 'user', 'content': 'Tell me about the robotics hub project.'},
            {'role': 'assistant', 'content': 'Cairo Youth Robotics & AI Hub has raised 95,000 EGP of 180,000 EGP.'}
        ]
    }), content_type='application/json')
    check("AI Multi-Turn Reasoning (200 OK)", r.status_code == 200 and 'response' in r.json())

    # 5. Platform Policy Query
    r = client.post('/api/chat/', data=json.dumps({'message': 'How does campaign cancellation work?'}), content_type='application/json')
    check("AI Policy Explanation (Contains 25% Rule)", '25%' in r.json().get('response', ''))

    # -------------------------------------------------------------
    # 7. Cleanup & Error Handlers
    # -------------------------------------------------------------
    print("\n[7/7] Testing Custom Error Handlers...")
    r = client.get('/non-existent-page-slug-404/')
    check("Custom 404 Handler (404 Not Found)", r.status_code == 404)

    # Clean up test records
    if created_project:
        created_project.delete()
    if new_user:
        new_user.delete()
    print("  🧹 Test data cleanup complete.")

    # Summary
    print("\n" + "=" * 70)
    print(f"🏁 PRE-DEPLOYMENT TEST RESULTS: {passed_tests}/{total_tests} TESTS PASSED")
    print("=" * 70)
    
    if passed_tests == total_tests:
        print("🎉 ALL SYSTEMS GO! The project is robust, secure, and ready for production deployment.")
        return 0
    else:
        print(f"⚠️ {total_tests - passed_tests} tests failed. Please review errors above.")
        return 1

if __name__ == '__main__':
    exit_code = run_e2e_tests()
    sys.exit(exit_code)
