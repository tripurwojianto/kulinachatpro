#!/bin/bash
case "$1" in
  gemini)
    MODEL="gemini-2.0-flash-lite"
    ;;
  gpt)
    MODEL="gpt-4o"
    ;;
  *)
    echo "Pilihan: gemini | gpt"
    exit 1
    ;;
esac

sed -i "s|model: str = Field(default=\".*\")|model: str = Field(default=\"$MODEL\")|" \
  ~/delisa-lazizah/customer_service/config.py

echo "✅ Model diganti ke: $MODEL"
grep "model: str" ~/delisa-lazizah/customer_service/config.py
