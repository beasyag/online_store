from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, DetailView
from django.template.response import TemplateResponse
from .models import Category, Product, Size, HeroVideo, Subcategory
from .services import (
    get_personalized_products,
    get_recently_viewed_products,
    get_similar_customer_products,
    get_trending_products,
    record_product_view,
)
from django.db.models import Q


class CatalogView(TemplateView):
    template_name = 'main/catalog_page.html'

    FILTER_MAPPING = {
        'color': lambda qs, v: qs.filter(color__iexact=v),
        'min_price': lambda qs, v: qs.filter(price__gte=v),
        'max_price': lambda qs, v: qs.filter(price__lte=v),
        'size': lambda qs, v: qs.filter(product_sizes__size__name=v),
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = kwargs.get('category_slug')
        subcategory_slug = kwargs.get('subcategory_slug')  # ← новое

        products = Product.objects.all().order_by('-created_at')
        current_subcategory = None

        if category_slug:
            get_object_or_404(Category, slug=category_slug)
            products = products.filter(category__slug=category_slug)

        if subcategory_slug:
            current_subcategory = get_object_or_404(
                Subcategory,
                slug=subcategory_slug,
                category__slug=category_slug
            )
            products = products.filter(subcategory=current_subcategory)

        query = self.request.GET.get('q')
        if query:
            products = products.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )

        filter_params = {}
        for param, filter_func in self.FILTER_MAPPING.items():
            value = self.request.GET.get(param)
            if value:
                products = filter_func(products, value)
                filter_params[param] = value
            else:
                filter_params[param] = ''

        filter_params['q'] = query or ''
        products = products.distinct()
        has_active_filters = bool(category_slug or subcategory_slug or query or any(
            filter_params.get(key) for key in self.FILTER_MAPPING
        ))

        context.update({
            'products': products,
            'current_category': category_slug,
            'current_subcategory': current_subcategory,
            'filter_params': filter_params,
            'sizes': Size.objects.all(),
            'search_query': query or '',
            'catalog_personalized_products': get_personalized_products(
                user=self.request.user,
                limit=4,
                exclude_ids=list(products.values_list('id', flat=True)) if has_active_filters else [],
            ),
        })

        if self.request.GET.get('show_search') == 'true':
            context['show_search'] = True
        elif self.request.GET.get('reset_search') == 'true':
            context['reset_search'] = True

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if request.headers.get('HX-Request'):
            if context.get('show_search'):
                return TemplateResponse(request, 'main/search_input.html', context)
            elif context.get('reset_search'):
                return TemplateResponse(request, 'main/search_button.html', {})
            template = (
                'main/filter_modal.html'
                if request.GET.get('show_filters') == 'true'
                else 'main/catalog.html'
            )
            return TemplateResponse(request, template, context)
        return TemplateResponse(request, self.template_name, context)


class IndexView(TemplateView):
    template_name = 'main/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['current_category'] = None
        featured_products = Product.objects.order_by('-created_at')[:4]
        context['featured_products'] = featured_products
        context['hero_video'] = HeroVideo.objects.filter(is_active=True).first()

        featured_ids = [p.id for p in featured_products]
        recommended_products = get_personalized_products(
            user=self.request.user,
            limit=4,
            exclude_ids=featured_ids,
        )
        continue_exploring_products = get_recently_viewed_products(
            user=self.request.user,
            limit=4,
            exclude_ids=featured_ids,
        )
        similar_customer_products = get_similar_customer_products(
            user=self.request.user,
            limit=4,
            exclude_ids=featured_ids,
        )
        rec_title = "Recommended for You" if self.request.user.is_authenticated else "Trending Now"
        if not recommended_products:
            recommended_products = list(get_trending_products(limit=4, exclude_ids=featured_ids))
            rec_title = "Trending Now"

        context['recommended_products'] = recommended_products
        context['rec_title'] = rec_title
        context['continue_exploring_products'] = continue_exploring_products
        context['similar_customer_products'] = similar_customer_products

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if request.headers.get('HX-Request'):
            return TemplateResponse(request, 'main/home_content.html', context)
        return TemplateResponse(request, self.template_name, context)

class ProductDetailView(DetailView):
    model = Product
    template_name = 'main/product_page.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        personalized_related = get_personalized_products(
            user=self.request.user,
            limit=4,
            exclude_ids=[product.id],
        )
        if personalized_related:
            context['related_products'] = personalized_related
            context['related_products_title'] = 'Picked for You'
        else:
            context['related_products'] = Product.objects.filter(
                category=product.category
            ).exclude(id=product.id)[:4]
            context['related_products_title'] = 'You May Also Like'
        context['current_category'] = product.category.slug
        context['needs_size_selection'] = product.product_sizes.filter(
            stock__gt=0
        ).exists()
        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        record_product_view(request.user, self.object)
        context = self.get_context_data(**kwargs)
        if request.headers.get('HX-Request'):
            return TemplateResponse(request, 'main/product_detail.html', context)
        return TemplateResponse(request, self.template_name, context)
