# views.py

from django.urls import reverse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from rest_framework.views import APIView
from rest_framework.response import Response

# Google OAuth2 settings
CLIENT_ID = 'YOUR_CLIENT_ID.apps.googleusercontent.com'
CLIENT_SECRET = 'YOUR_CLIENT_SECRET'
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
REDIRECT_URI = 'http://localhost:8000/rest/v1/calendar/redirect/'

class GoogleCalendarInitView(APIView):
    def get(self, request):
        # Create the OAuth2 flow instance
        flow = Flow.from_client_config(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, scopes=SCOPES, redirect_uri=REDIRECT_URI)

        # Generate the authorization URL
        authorization_url, state = flow.authorization_url(prompt='consent')

        # Store the state in the session
        request.session['google_oauth2_state'] = state

        # Return the authorization URL as a response
        return Response({'authorization_url': authorization_url})


class GoogleCalendarRedirectView(APIView):
    def get(self, request):
        # Check for errors in the OAuth2 response
        error = request.GET.get('error')
        if error:
            return Response({'error': error})

        # Check the state to protect against cross-site request forgery attacks
        state = request.GET.get('state')
        if state != request.session.get('google_oauth2_state'):
            return Response({'error': 'Invalid state parameter'})

        # Exchange the authorization code for an access token
        code = request.GET.get('code')
        flow = Flow.from_client_config(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, scopes=SCOPES, redirect_uri=REDIRECT_URI)
        flow.fetch_token(code=code)

        # Use the access token to get the user's calendar events
        credentials = Credentials.from_authorized_user_info(info=flow.credentials.to_json())
        service = build('calendar', 'v3', credentials=credentials)
        events_result = service.events().list(calendarId='primary', timeMin='2023-04-22T00:00:00Z', timeMax='2023-04-23T00:00:00Z', maxResults=10, singleEvents=True, orderBy='startTime').execute()
        events = events_result.get('items', [])

        # Return the events as a response
        return Response({'events': events})
