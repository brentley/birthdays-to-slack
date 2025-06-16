#!/bin/bash
# Clear all generated messages to force regeneration with new prompt

echo "🗑️  Clearing all generated messages..."

# Stop containers
docker compose stop birthdays-to-slack

# Remove generated messages file
if [ -f "data/generated_messages.json" ]; then
    rm -f data/generated_messages.json
    echo "✅ Removed generated_messages.json"
fi

# Also update the prompt file with the new template
cat > data/birthday_prompt.txt << 'EOF'
Write a birthday message for {employee_name} whose birthday is {birthday_date}. Include an interesting positive historical fact from this date (with specific year). Connect the historical event to their birthday in a creative way. Keep it professional, warm, and fun.

Rules:
1. Start with the historical fact (e.g., "On June 21, 1982, Prince William was born...")
2. Transition smoothly to birthday wishes without mentioning birth year
3. Avoid phrases like "unknown year", "wink", "won't mention", or obvious age-hiding
4. Keep it natural and conversational
5. Use emojis sparingly
6. 2-3 sentences total

Good example: "On June 21, 1982, Prince William was born, bringing joy to millions! Speaking of royalty, let's celebrate our own {employee_name} today. Happy Birthday!"

Bad example: "On June 21, 1982, something happened, and in a year we won't mention (wink), {employee_name} was born..."
EOF

echo "✅ Updated prompt template"

# Restart containers
docker compose start birthdays-to-slack

echo ""
echo "🎉 Done! Messages will be regenerated with the new prompt."
echo "Give it a minute to regenerate, then refresh the web UI."