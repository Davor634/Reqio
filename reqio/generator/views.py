from django.shortcuts import render, redirect
from .forms import SignUpForm
from django.contrib.auth import login
from .models import SRSDocument, Profile
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
from .utils.openai_integration import get_assistant
from openai import OpenAI
import os
import logging
from django.http import HttpResponse
from django.conf import settings

template = '{"Introduction": {"Purpose": "...","Document Conventions": "...","Intended Audience": "...","Project Scope": "..."},"Overall Description": {"Product Perspective": "...","Product Functions": {"...": "...","...": "...","...": "...",...},"User Classes and Characteristics": {"...(Class 1)": "...","...(Class 2)": "...","...(Class 3)": "..."},"Operating Environment": "...","Design and Implementation Constraints": {"Technologies": "..., ...","Compliance": "..., ..."},"User Documentation": "...","Assumptions and Dependencies": "..."},"System Features": {"...(System feature 1)": {"Description": "...","Functional Requirements": {"1": "...","2": "...","3": "..."}},"...(System feature 2)": {"Description": "...","Functional Requirements": {"1": "...","2": "..."}},"...(System feature 3)": {"Description": "...","Functional Requirements": {"1": "...","2": "..."}},..},"External Interface Requirements": {"User Interfaces": "...","Hardware Interfaces": "...","Software Interfaces": "...","Communications Interfaces": "..."},"Nonfunctional Requirements": {"...":"...","...":"..."}}'
logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)
assistant_id = get_assistant()  


def home(request):
    
    return render(request, 'generator/homepage.html')

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def profile(request):
    return render(request, 'generator/profilepage.html')


@login_required
def load_saved(request):

    scopes = []
    apps = SRSDocument.objects.filter(user=request.user.id)
    zipped_list = None
    document = None

    if apps is not None:
        for app in apps:
            scope = app.document.get('Introduction')
            temp = None

            for key in scope.keys():
                if 'scope' in key.lower():
                    temp = scope[key]
                
                    
            scopes.append(temp)

        zipped_list = zip(apps, scopes)
        document = app.document

    context = {
        'zipped_list':zipped_list,
        'document':document,
    }
    return render(request, 'generator/saved_apps.html', context)

@login_required
def app_detail(request, app_id):
    app = SRSDocument.objects.get(id=app_id)
    document = app.document
    document = json.dumps(document)
    context = {
        'app': app,
        'document':document,
    }
    return render(request, 'generator/app_detail.html', context)

@login_required
def save(request, app_id):
    if request.method == 'POST':
        
        app = SRSDocument.objects.get(pk=app_id)
        json_data = json.loads(request.body)            
        app.document = json_data
        app.save()

        app = SRSDocument.objects.get(pk=app_id)

        context = {
            'app': app,
            'document': app.document,  
        }

        return redirect('generator:app_detail', app_id=app_id, permanent=True)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    
@login_required
def create(request):
    thread_id = request.session.get('thread_id', None)

    if thread_id is not None:
        document = SRSDocument.objects.get(thread_id=thread_id)
    else:
        del request.session['thread_id']

    if document.document is not None:
        del request.session['thread_id']

    return render(request, 'generator/creationpage.html')

@login_required
def assistant_response(request):

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == "POST":
        
        user_input = request.POST.get('prompt', '')
        name = request.POST.get('name', '')

        try:
            thread_id = request.session.get('thread_id', None)
            if not thread_id:
                thread = client.beta.threads.create()
                request.session['thread_id'] = thread.id
                thread_id = thread.id
            message = client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=user_input + ' ask as many questions as you can'
            )
            run = client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id,
            )
            completed_run = client.beta.threads.runs.retrieve(run.id, thread_id=thread_id)
            while completed_run.status not in ['completed', 'failed']:
                logger.error(f"Generating ")
                completed_run = client.beta.threads.runs.retrieve(run.id, thread_id=thread_id)

            if completed_run.status == 'completed':
                response_text = client.beta.threads.messages.list(thread_id).data[0].content[-1].text.value
                questions = json.loads(response_text)
            else:
                response_text = "Failed to get a response from the assistant."
        except Exception as e:
            logger.error(f"Error in processing the request: {str(e)}")
            response_text = "Failed to get a response due to an error."

        document = SRSDocument(user = request.user, thread_id = thread_id, name = name, prompt = user_input, document = None ,questions=questions)
        document.save()

        return JsonResponse({'response': response_text})
    elif request.method == 'GET':
        thread_id = request.session.get('thread_id', None)
        response_text = None
        document = None
        
        if thread_id is not None:
            document = SRSDocument.objects.get(thread_id=thread_id)

        if document is not None and document.document is not None:
            del request.session['thread_id']
            thread_id = request.session.get('thread_id', None)
        if thread_id is not None:
            response_text = client.beta.threads.messages.list(thread_id).data[0].content[-1].text.value


        context = {'response': response_text}

    return render(request, 'generator/creationpage.html', context)



@login_required
def submit_questions(request):
    if request.method == 'POST':

        thread_id = request.session.get('thread_id', None)
        document = SRSDocument.objects.get(thread_id=thread_id)

        if request.POST['action'] == 'Reset':
            document.delete()
            if 'thread_id' in request.session:
                del request.session['thread_id']
            return redirect("generator:home")
        elif request.POST['action'] == 'Answer': 
            answers = {key: request.POST[key] for key in request.POST.keys() if key.startswith('answer_')}
            answers = json.dumps(answers)
            answers = answers + " draft a detailed document based on this template: " + template + " and return a JSON object"
        elif request.POST['action'] == 'Let the Assistant decide':
            answers = "Answer the questions to the best of your ability and draft a detailed document based on this template: " + template + " and return a JSON object"

        
        try:
            thread_id = request.session.get('thread_id', None)
            if not thread_id:
                thread = client.beta.threads.create()
                request.session['thread_id'] = thread.id
                thread_id = thread.id

            message = client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=answers
            )
            run = client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id,
            )

            completed_run = client.beta.threads.runs.retrieve(run.id, thread_id=thread_id)
            while completed_run.status not in ['completed', 'failed']:
                logger.error(f"Generating ")
                completed_run = client.beta.threads.runs.retrieve(run.id, thread_id=thread_id)

            if completed_run.status == 'completed':
                response_text = client.beta.threads.messages.list(thread_id).data[0].content[-1].text.value
                data = json.loads(response_text)
                document.document = data
                document.save()
            else:
                response_text = "Failed to get a response from the assistant."

        except Exception as e:
            logger.error(f"Error in processing the request: {str(e)}")
            response_text = "Failed to get a response due to an error."

        return redirect("generator:app_detail", document.id)
    else:
        return HttpResponse("Method not allowed", status=405)
    
@login_required
def change(request, app_id):
    if request.method == "POST":

        app = SRSDocument.objects.get(id=app_id)

        user_input = request.POST['user_input']
        
        document = SRSDocument.objects.get(id = app_id)
        thread_id = document.thread_id
        response_text = None
        data = None
        
        try:
            message = client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=user_input + '\n Apply the changes to this document: ' + json.dumps(app.document) + ' and return the entire document'
            )
            run = client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id,
            )

            completed_run = client.beta.threads.runs.retrieve(run.id, thread_id=thread_id)
            while completed_run.status not in ['completed', 'failed']:
                logger.error(f"Generating ")
                completed_run = client.beta.threads.runs.retrieve(run.id, thread_id=thread_id)

            if completed_run.status == 'completed':
                response_text = client.beta.threads.messages.list(thread_id).data[0].content[-1].text.value
                data = json.loads(response_text)
                data = json.dumps(data)
            else:
                response_text = "Failed to get a response from the assistant."

        except Exception as e:
            logger.error(f"Error in processing the request: {str(e)}")
            response_text = "Failed to get a response due to an error."
        

        app.changed_document = json.loads(data)
        document = json.dumps(app.document)
        app.save()
        

        context = {
            'app': app,
            'document':document,
            'data':data
        }

        return render(request, 'generator/app_detail.html', context)

    else:
        return redirect("generator:app_detail", app_id)
    
@login_required
def apply(request, app_id):

    app = SRSDocument.objects.get(id=app_id)

    if request.POST['action'] == 'Apply': 

        data = app.changed_document
        app.changed_document=None
        app.document = data
        app.save()

        return redirect("generator:app_detail", app_id)
    elif request.POST['action'] == 'Discard':
        
        app.changed_document=None
        app.save()

        return redirect("generator:app_detail", app_id)
    
@login_required
def delete(request, app_id):
    if(request.method == 'POST'):
        app = SRSDocument.objects.get(id=app_id)
        app.delete()
        if 'thread_id' in request.session:
            del request.session['thread_id']

    return redirect("generator:saved")