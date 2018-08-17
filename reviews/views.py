from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Review, Wine, Cluster
from .forms import ReviewForm
from .suggestions import update_clusters
import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

# Create your views here.
def user_review_list(request, username=None):
    if not username:
        username = request.user.username
    latest_review_list = Review.objects.filter(user_name=username).order_by('-pub_date')
    context = {'latest_review_list':latest_review_list, 'username':username}
    return render(request, 'reviews/user_review_list.html', context)    

def review_list(request):
    latest_review_list = Review.objects.order_by('-pub_date')[:9]
    context = {'latest_review_list':latest_review_list}
    return render(request, 'reviews/review_list.html', context)

def review_detail(request, review_id):
    review = get_object_or_404(Review, pk = review_id)
    return render(request, 'reviews/review_detail.html', {'review':review})

def wine_list(request):
    wine_list = Wine.objects.order_by('-name')
    context = {'wine_list':wine_list}
    return render(request,'reviews/wine_list.html', context)

def wine_detail(request, wine_id):
    wine = get_object_or_404(Wine, pk = wine_id)
    form = ReviewForm()
    return render(request, 'reviews/wine_detail.html', {'wine':wine, 'form': form})

@login_required
def add_review(request, wine_id):
    wine = get_object_or_404(Wine, pk = wine_id)
    form = ReviewForm(request.POST)
    if form.is_valid():
        rating = form.cleaned_data['rating']
        comment = form.cleaned_data['comment']
        user_name = request.user.username
        review = Review()
        review.wine = wine
        review.user_name = user_name
        review.comment = comment
        review.rating = rating
        review.pub_date = datetime.datetime.now()
        review.save()
        update_clusters()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('reviews:wine_detail', args=[wine.id]))
    return render(request, 'reviews/wine_detail.html', {'wine':wine, 'form': form})

@login_required
def user_recommendation_list(request):
    # get this user reviews
    user_reviews = Review.objects.filter(user_name=request.user.username).prefetch_related('wine')
    # from the reviews, get set of wines
    user_reviews_wine_ids = set(map(lambda x: x.wine.id, user_reviews))

    # get request user first cluster name
    try:
        user_cluster_name = User.objects.get(username=request.user.username).cluster_set.first().name
    except: # if no cluster has been assigned for a user, update clusters
        update_clusters()
        user_cluster_name = User.objects.get(username=request.user.username).cluster_set.first().name        

    # get usernames of the other members of the cluster
    user_cluster_other_members = Cluster.objects.get(name=user_cluster_name).users.exclude(username=request.user.username).all()
    other_members_usernames = set(map(lambda x: x.username, user_cluster_other_members))

    # get reviews by those other users, excluding wines reviewed by the request user
    other_users_reviews = Review.objects.filter(user_name__in=other_members_usernames).exclude(wine__id__in=user_reviews_wine_ids)
    other_users_reviews_wine_ids = set(map(lambda x: x.wine_id, other_users_reviews))

    # TODO: then get a wine list including the previous IDS, order by rating
    # wine_list = sorted(
    #     list(Wine.objects.filter(id__in=other_users_reviews_wine_ids)),
    #     key = lambda x: x.average_rating,
    #     reverse = True
    # ) 

    wine_list =list(Wine.objects.filter(id__in=other_users_reviews_wine_ids)) 
    return render(request, 'reviews/user_recommendation_list.html', {'username': request.user.username, 'wine_list': wine_list})
