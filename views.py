import requests
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

API_KEY = "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"

from .models import Conversation, Message
from django.shortcuts import redirect

@login_required
def home(request):
    response_text = None

    # ---- HANDLE NEW CONVERSATION ----
    if request.GET.get("new"):
        conversation = Conversation.objects.create(user=request.user)
        request.session["conversation_id"] = conversation.id
        return redirect("home")

    # ---- HANDLE SWITCH CONVERSATION ----
    if request.GET.get("conversation"):
        request.session["conversation_id"] = int(request.GET.get("conversation"))
        return redirect("home")

    # ---- GET CURRENT CONVERSATION ----
    if "conversation_id" not in request.session:
        conversation = Conversation.objects.create(user = request.user)
        request.session["conversation_id"] = conversation.id
    else:
        conversation = Conversation.objects.get(
    id=request.session["conversation_id"],
    user=request.user

)

    # ---- HANDLE CHAT MESSAGE ----
    if request.method == "POST" and request.POST.get("message"):
        user_input = request.POST.get("message")

        Message.objects.create(
            conversation=conversation,
            role="user",
            content=user_input
        )

        crisis_words = ["suicide", "kill myself", "end my life", "self harm", "i want to die"]

        if any(word in user_input.lower() for word in crisis_words):
            response_text = (
                "⚠️ If you are in immediate danger, please seek help immediately.\n\n"
                "📞 India Mental Health Helpline: 9152987821\n"
                "📞 Emergency: 112\n\n"
                "You are not alone."
            )
        else:
            messages = [
                {"role": msg.role, "content": msg.content}
                for msg in conversation.messages.all().order_by("timestamp")
            ]

            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }

            data = {
                "model": "mistralai/mistral-7b-instruct",
                "messages": messages
            }

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data
            )

            result = response.json()
            response_text = result["choices"][0]["message"]["content"]

        Message.objects.create(
            conversation=conversation,
            role="assistant",
            content=response_text
        )

    # Load all conversations
    conversations = Conversation.objects.filter(
    user=request.user
).order_by("-created_at")
    messages = conversation.messages.all().order_by("timestamp")

    return render(request, "chatbot/home.html", {
        "response": response_text,
        "conversations": conversations,
        "current_conversation": conversation,
        "messages": messages
    })