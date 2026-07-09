resource "aws_s3_bucket" "data_lake" {
  bucket = "nariman-osman-data-lake"
}

resource "aws_lambda_function" "validation_pipeline" {
  function_name = "Nariman-Data-Validation-Pipeline"
  role          = "arn:aws:iam::229705501595:role/Nariman-Lambda-Validation-Role"
  filename      = "../lambda_deploy.zip"
  
  runtime       = "python3.12"
  handler       = "lambda_function.lambda_handler"
  timeout       = 30
  
  # Add this to match AWS and prevent the "change"
  description   = "Validates raw data incoming files for 9 columns before storage shift."
}


resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.validation_pipeline.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.data_lake.arn
}


resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.data_lake.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.validation_pipeline.arn
    events              = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.allow_bucket]
}