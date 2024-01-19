deploy:
	gcloud app deploy --project forthsalon-hrd

deps:
	pip install -t lib -r requirements.txt

server:
	GOOGLE_CLOUD_PROJECT=forthsalon-hrd python3 /usr/lib/google-cloud-sdk/bin/dev_appserver.py --log_level debug .
