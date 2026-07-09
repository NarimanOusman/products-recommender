# products-recommender

End-to-end machine learning product recommendation project with:

- a model-serving UI built with Django
- a shared validation layer for Django and AWS Lambda
- trained artifacts stored in `model.pkl` and `label_encoder.pkl`
- infrastructure kept separately in `terraform/`

## Local Run

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Run the Django app from the `django_backend/` folder:

   ```bash
   python manage.py runserver
   ```

3. Open the homepage and submit the prediction form.

## Notes

- The Lambda validation pipeline and Django request validation share the same helper logic in `shared/validation.py`.
- The model expects the engineered feature payload defined in that shared module.
