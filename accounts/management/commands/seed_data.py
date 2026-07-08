"""
Seed the database with sample data for development.

Usage: python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from accounts.models import CustomUser
from vehicles.models import Car, CarImage
from leads.models import Lead, Appointment
from notifications.models import SmsLog
from chatbot.models import ChatSession, ChatMessage
from campaigns.models import Campaign, CampaignRecipient
from datetime import datetime, timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Seed the database with sample data for development'

    def handle(self, *args, **options):
        now = timezone.now()

        self.stdout.write('Creating staff users...')
        admin = CustomUser.objects.create_user(
            phone='+255711000001', password='admin123',
            full_name='Admin User', is_staff=True, is_superuser=True, is_customer=False,
        )
        marketing = CustomUser.objects.create_user(
            phone='+255711000002', password='marketing123',
            full_name='Marketing User', is_staff=True, is_customer=False,
        )
        sales = CustomUser.objects.create_user(
            phone='+255711000003', password='sales123',
            full_name='Sales User', is_staff=True, is_customer=False,
        )
        support = CustomUser.objects.create_user(
            phone='+255711000004', password='support123',
            full_name='Support User', is_staff=True, is_customer=False,
        )

        admin_group = Group.objects.get(name='Admin')
        marketing_group = Group.objects.get(name='Marketing')
        sales_group = Group.objects.get(name='Sales')
        support_group = Group.objects.get(name='Support')

        admin.groups.add(admin_group)
        marketing.groups.add(marketing_group)
        sales.groups.add(sales_group)
        support.groups.add(support_group)

        self.stdout.write('  Admin: +255711000001 / admin123')
        self.stdout.write('  Marketing: +255711000002 / marketing123')
        self.stdout.write('  Sales: +255711000003 / sales123')
        self.stdout.write('  Support: +255711000004 / support123')

        self.stdout.write('Creating customers...')
        customer1 = CustomUser.objects.create_user(
            phone='+255712000001', full_name='Juma Mwangi', is_customer=True,
        )
        customer2 = CustomUser.objects.create_user(
            phone='+255712000002', full_name='Aisha Mohamed', is_customer=True,
        )

        self.stdout.write('Creating cars...')
        cars_data = [
            ('Toyota', 'Hilux', 2023, 95000000, 'Double cabin, diesel, 4x4, excellent condition. Full service history.', 'https://images.unsplash.com/photo-1583267746897-2cf415887172?w=800'),
            ('Toyota', 'Land Cruiser Prado', 2022, 180000000, 'TX-L trim, 7 seats, leather interior, sunroof.', 'https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?w=800'),
            ('Nissan', 'X-Trail', 2023, 65000000, 'SV trim, 5 seats, 4WD, panoramic roof, low mileage.', 'https://images.unsplash.com/photo-1549399542-7e3f8b79c341?w=800'),
            ('Suzuki', 'Swift', 2024, 28000000, 'GL trim, 5-speed manual, fuel efficient, perfect for city driving.', 'https://images.unsplash.com/photo-1583121274602-3e2820c69888?w=800'),
            ('BMW', 'X5', 2021, 150000000, 'xDrive40i, M Sport package, 7 seats, luxury SUV.', 'https://images.unsplash.com/photo-1555215695-3004980ad54e?w=800'),
            ('Mercedes-Benz', 'C-Class', 2023, 85000000, 'C200 Avantgarde, AMG line, low mileage, mint condition.', 'https://images.unsplash.com/photo-1617654112368-307921291f42?w=800'),
            ('Honda', 'CR-V', 2022, 72000000, 'Touring trim, 5 seats, AWD, Honda Sensing safety suite.', 'https://images.unsplash.com/photo-1568844293986-ca474826b59d?w=800'),
            ('Mitsubishi', 'Outlander', 2023, 58000000, 'PHEV, 7 seats, leather, 360 camera, hybrid fuel savings.', 'https://images.unsplash.com/photo-1533106418989-7cf8a13ecafe?w=800'),
        ]

        cars = []
        for make, model, year, price, desc, img_url in cars_data:
            car = Car.objects.create(
                make=make, model=model, year=year, price=price,
                status='available', description=desc,
            )
            CarImage.objects.create(car=car, image_url=img_url, is_primary=True)
            cars.append(car)
            self.stdout.write(f'  {make} {model} ({year}) - TZS {price:,}')

        self.stdout.write('Creating leads...')
        lead1 = Lead.objects.create(
            customer=customer1, phone='+255712000001',
            full_name='Juma Mwangi', source='website',
            interested_car=cars[0], status='qualified', assigned_to=sales,
        )
        lead2 = Lead.objects.create(
            phone='+255713000001', full_name='Halima Salim',
            source='chatbot', interested_car=cars[1], status='new',
        )
        lead3 = Lead.objects.create(
            customer=customer2, phone='+255712000002',
            full_name='Aisha Mohamed', source='website',
            interested_car=cars[2], status='contacted', assigned_to=sales,
        )

        self.stdout.write('Creating appointments...')
        Appointment.objects.create(
            lead=lead1, car=cars[0], type='test_drive',
            scheduled_at=now + timedelta(days=2), status='confirmed',
        )
        Appointment.objects.create(
            lead=lead2, car=cars[1], type='call_back',
            scheduled_at=now + timedelta(days=1), status='pending',
        )

        self.stdout.write('Creating sample SMS logs...')
        SmsLog.objects.create(
            phone='+255712000001', message='Your verification code is 482910.',
            status='sent', provider_message_id='msg-001',
        )
        SmsLog.objects.create(
            phone='+255712000002',
            message='Your test drive for Toyota Hilux is booked for Friday, 14 June at 10:00.',
            status='delivered', provider_message_id='msg-002',
        )

        self.stdout.write('Creating chatbot sessions...')
        session = ChatSession.objects.create(lead=lead2, phone='+255713000001')
        ChatMessage.objects.create(session=session, sender='customer', message='Hi, how much is the Prado?')
        ChatMessage.objects.create(session=session, sender='bot', message='The Toyota Land Cruiser Prado (2022) is priced at TZS 180,000,000. Would you like to book a test drive?')

        self.stdout.write('Creating sample campaign...')
        campaign = Campaign.objects.create(
            name='End of Year Sale',
            message_template='Hello {full_name}! Visit our showroom this weekend for special discounts on all Toyota models. Call us for details.',
            created_by=marketing, status='draft',
        )
        CampaignRecipient.objects.create(campaign=campaign, lead=lead1, phone=lead1.phone)
        CampaignRecipient.objects.create(campaign=campaign, lead=lead2, phone=lead2.phone)

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
