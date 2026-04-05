from django.test import TestCase
from django.urls import reverse

from chat.models import Conversation
from sellers.models import Seller
from users.models import CustomUser


class ChatAccessTests(TestCase):
    def setUp(self):
        self.owner = CustomUser.objects.create_user(
            email='owner@example.com',
            first_name='Owner',
            last_name='User',
            password='testpass123',
        )
        self.other_user = CustomUser.objects.create_user(
            email='other@example.com',
            first_name='Other',
            last_name='User',
            password='testpass123',
        )
        seller_user = CustomUser.objects.create_user(
            email='seller@example.com',
            first_name='Seller',
            last_name='User',
            password='testpass123',
            role='seller',
        )
        seller = Seller.objects.create(
            user=seller_user,
            shop_name='Seller Shop',
            shop_slug='seller-shop',
            status='verified',
        )
        self.conversation = Conversation.objects.create(buyer=self.owner, seller=seller)

    def test_user_cannot_view_foreign_conversation(self):
        self.client.force_login(self.other_user)
        response = self.client.get(reverse('chat:detail', kwargs={'conversation_id': self.conversation.id}))

        self.assertEqual(response.status_code, 404)
