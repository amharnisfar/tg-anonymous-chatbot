<!DOCTYPE html>
<html>
<body style="font-family: sans-serif;">
<h1>Advanced Telegram Anonymous ChatBot Including AI - By Amhar Nisfer</h1>
<p>This is a sophisticated Telegram bot that connects users for anonymous chats, complete with gender-based pairing and a direct line to a generative AI assistant named Rosi. It features a full user onboarding process, admin-specific commands, and a robust architecture designed for scalability.</p>
<a href="https://t.me/aharchatbot" target="_blank" style="display: inline-block; background-color: #0088cc; color: #ffffff; padding: 12px 20px; margin: 10px 0; text-align: center; text-decoration: none; font-size: 16px; border-radius: 5px; font-weight: bold;">Message Bot on Telegram</a>
<hr>
<h2>✨ Features</h2>
<ul>
<li><strong>👤 User Onboarding:</strong> A guided setup process to collect user name, gender, age, and location.</li>
<li><strong>💬 Anonymous Chat:</strong> Connects two random users for a one-on-one conversation.</li>
<li><strong>⚤ Gender-Based Pairing:</strong> Users can choose to be connected specifically with a male or female partner.</li>
<li><strong>🤖 AI Assistant ("Rosi"):</strong> Users can chat directly with a helpful AI powered by Google's Generative AI.</li>
<li><strong>🔐 Privacy Focused:</strong> Forwards messages without revealing user identities and protects content from being forwarded.</li>
<li><strong>🛠️ Admin Panel:</strong> Special commands for the bot admin to view usage statistics and manage API keys.</li>
<li><strong>🚀 Robust & Asynchronous:</strong> Built with <code>asyncio</code> to handle many conversations concurrently without blocking.</li>
<li><strong>🐳 Dockerized:</strong> Comes with a complete Dockerfile for easy and consistent deployment.</li>
<li><strong>❤️ Health Check:</strong> Includes a Flask web server to provide a health check endpoint, perfect for modern hosting platforms.</li>
</ul>
<hr>
<h2>🛠️ Project Structure</h2>
<p>The bot is organized into several key files:</p>
<pre><code style="background-color: #f1f1f1; display: block; padding: 10px;">/your-project
├── Dockerfile
├── requirements.txt
├── bot.py
├── UserStatus.py
└── db_connection.py
</code></pre>
<ul>
<li><code>bot.py</code>: The main application logic, containing all handlers and the bot's core functionality.</li>
<li><code>db_connection.py</code>: Manages all interactions with the SQLite database.</li>
<li><code>UserStatus.py</code>: Contains the <code>Enum</code> for managing user states (e.g., IDLE, IN_SEARCH, COUPLED).</li>
<li><code>requirements.txt</code>: Lists all the Python packages required to run the bot.</li>
<li><code>Dockerfile</code>: Instructions to build the container image for deployment.</li>
</ul>
<hr>
<h2>🚀 Deployment</h2>
<p>You can run this bot either inside a Docker container (recommended for production) or directly on your local machine for development and testing.</p>
<h3><strong>🐳 How to Run Using Docker (Production)</strong></h3>
<p>Docker is the recommended way to run this bot in production for consistency and ease of management.</p>
<h4><strong>1. Build the Docker Image</strong></h4>
<p>From the root directory of the project, run the following command:</p>
<pre><code style="background-color: #f1f1f1; display: block; padding: 10px;">docker build -t telegram-chat-bot .</code></pre>
<h4><strong>2. Run the Docker Container</strong></h4>
<p>Run the container by providing your credentials as environment variables. This is the most secure method.</p>
<pre><code style="background-color: #f1f1f1; display: block; padding: 10px;">docker run -d --name my-chat-bot \
  -e BOT_TOKEN="YOUR_ACTUAL_BOT_TOKEN" \
  -e ADMIN_ID="YOUR_ACTUAL_ADMIN_ID" \
  -e BOT_OWNER_CONTACT="@YourAdminUsername" \
  -e GOOGLE_AI_API_KEY="YOUR_ACTUAL_GOOGLE_AI_KEY" \
  -p 8080:8080 \
  telegram-chat-bot
</code></pre>
<p>Your bot is now running in the background!</p>
<h3><strong>💻 How to Run Locally (for Development)</strong></h3>
<p>Follow these steps to run the bot on your own machine. This is ideal for testing and development.</p>
<h4><strong>1. Create a Virtual Environment</strong></h4>
<p>It's a best practice to isolate your project's dependencies. From the project's root directory:</p>
<pre><code style="background-color: #f1f1f1; display: block; padding: 10px;"># Create the virtual environment
python3 -m venv venv

# Activate it (on MacOS/Linux)
source venv/bin/activate

# Or activate it (on Windows)
.\\venv\\Scripts\\activate
</code></pre>
<h4><strong>2. Install Dependencies</strong></h4>
<p>Install all the required Python libraries from the <code>requirements.txt</code> file.</p>
<pre><code style="background-color: #f1f1f1; display: block; padding: 10px;">pip install -r requirements.txt
</code></pre>
<h4><strong>3. Set Environment Variables</strong></h4>
<p>The bot reads credentials from environment variables. You must set them in your terminal session before running the script.</p>
<p><strong>On MacOS or Linux:</strong></p>
<pre><code style="background-color: #f1f1f1; display: block; padding: 10px;">export BOT_TOKEN="YOUR_ACTUAL_BOT_TOKEN"
export ADMIN_ID="YOUR_ACTUAL_ADMIN_ID"
export BOT_OWNER_CONTACT="@YourAdminUsername"
export GOOGLE_AI_API_KEY="YOUR_ACTUAL_GOOGLE_AI_KEY"
export HEALTH_CHECK_PORT="8080"
</code></pre>
<p><strong>On Windows (Command Prompt):</strong></p>
<pre><code style="background-color: #f1f1f1; display: block; padding: 10px;">set BOT_TOKEN="YOUR_ACTUAL_BOT_TOKEN"
set ADMIN_ID="YOUR_ACTUAL_ADMIN_ID"
set BOT_OWNER_CONTACT="@YourAdminUsername"
set GOOGLE_AI_API_KEY="YOUR_ACTUAL_GOOGLE_AI_KEY"
set HEALTH_CHECK_PORT="8080"
</code></pre>
<h4><strong>4. Run the Bot</strong></h4>
<p>With your virtual environment active and environment variables set, start the bot:</p>
<pre><code style="background-color: #f1f1f1; display: block; padding: 10px;">python bot.py
</code></pre>
<p>The bot is now running and connected to Telegram. To stop it, press <code>CTRL+C</code> in the terminal.</p>
<hr>
<h2>🤖 Bot Commands</h2>
<p>Here is a list of all available commands within the bot.</p>
<table border="1" style="width:100%; border-collapse: collapse;">
<thead>
<tr style="background-color: #f2f2f2;">
<th style="padding: 8px; text-align: left;">Category</th>
<th style="padding: 8px; text-align: left;">Command</th>
<th style="padding: 8px; text-align: left;">Description</th>
</tr>
</thead>
<tbody>
<tr>
<td rowspan="3"><strong>Profile & General</strong></td>
<td><code>/start</code></td>
<td>Starts the bot and begins the profile creation process.</td>
</tr>
<tr>
<td><code>/help</code></td>
<td>Shows the list of all available commands.</td>
</tr>
<tr>
<td><code>/contact</code></td>
<td>Displays contact information for the bot owner.</td>
</tr>
<tr>
<td rowspan="5"><strong>Human Chat</strong></td>
<td><code>/chat</code></td>
<td>Finds a random chat partner.</td>
</tr>
<tr>
<td><code>/chat_male</code></td>
<td>Finds a male chat partner.</td>
</tr>
<tr>
<td><code>/chat_female</code></td>
<td>Finds a female chat partner.</td>
</tr>
<tr>
<td><code>/exit</code></td>
<td>Leaves your current chat.</td>
</tr>
<tr>
<td><code>/newchat</code></td>
<td>Exits the current chat and immediately finds a new random partner.</td>
</tr>
<tr>
<td rowspan="2"><strong>AI Chat</strong></td>
<td><code>/aichat</code></td>
<td>Starts a conversation with Rosi, the AI assistant.</td>
</tr>
<tr>
<td><code>/exit_aichat</code></td>
<td>Ends your conversation with the AI.</td>
</tr>
<tr>
<td rowspan="2" style="background-color: #fffbe6;"><strong>Admin</strong></td>
<td style="background-color: #fffbe6;"><code>/stats</code></td>
<td style="background-color: #fffbe6;">(Admin Only) Displays bot usage statistics like total and active users.</td>
</tr>
<tr>
<td style="background-color: #fffbe6;"><code>/change_api_key <key></code></td>
<td style="background-color: #fffbe6;">(Admin Only) Updates the Google AI API key on the fly.</td>
</tr>
</tbody>
</table>
<hr>
<p>© 2025 Amhar Nisfer Dev, Inc.</p>
</body>
</html>
