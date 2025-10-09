Project title & short description:

QREntry: Seamless entry, powered by QR

The proposed Web-Based Event Ticketing System is an online platform that streamlines the process of purchasing and verifying event tickets. Attendees can browse events, choose tickets, make secure online payments, and instantly receive a unique QR code as their digital ticket, removing the need for paper tickets and manual confirmations. Organizers gain a centralized dashboard to manage events, track ticket sales, monitor attendance, and access real-time reports, while authorized staff can validate QR codes at the venue to ensure only legitimate ticket holders gain entry.

Tech stack used:

The system will be developed with Python and the Django framework for a secure and     scalable backend, using MySQL(Supabase) for efficient data management. The frontend will employ HTML5 and CSS to deliver a responsive, mobile-friendly interface, and Python libraries will handle QR code generation and validation.
Setup & Run Instructions
1. install Django
run this at terminal
pip install django

2. install git
3. git clone the copied link of the repository
git clone <repository_link>

4. change directory to QREntry project
cd <project_file_location>

5. create a .env file in the root directory of the project.
6. copy and paste this in .env file:
DATABASE_URL=postgresql://postgres.xmqzgsolehbtyyxplqom:QREntry420--@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres
SECRET_KEY=your_django_secret_key
DEBUG=True
7. run the server, input in terminal: python manage.py runserver
8. open in browser and go to: http://127.0.0.1:8000/

Team members:

John Harley Cruz (johnharley.cruz@cit.edu) - Lead Developer
Rocky Decretales Jr. (rocky.decretales@cit.edu) - Backend Developer
Alexandrei Nash Dinapo (alexandreinash.dinapo@cit.edu) - Frontend Developer
