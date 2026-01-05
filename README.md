<!DOCTYPE html>
<html>
<body style="font-family: sans-serif;">
<h1>Advanced Telegram Anonymous ChatBot Including AI - By Amhar Nisfer</h1>
<p>This is a sophisticated Telegram bot that connects users for anonymous chats and features a direct line to an advanced, tool-wielding AI assistant named Lisa. It includes a full user onboarding process, gender-based pairing, robust admin commands, and a powerful hybrid AI architecture designed for rich, interactive conversations.</p>
<div>
<a href="https://t.me/aharchatbot" target="_blank" style="display: inline-block; background-color: #0088cc; color: #ffffff; padding: 12px 20px; margin: 10px 0; text-align: center; text-decoration: none; font-size: 16px; border-radius: 5px; font-weight: bold;">Message Bot on Telegram</a>
</div>
<div>
<br>
<p><b>Host on Dipoi.com for Free - 14 days free trial (👇Click on the icon below👇)</b></p>
<a href="https://diploi.com/" target="_blank">
<center><img src="https://docs.diploi.com/_astro/logo-text.BLyLf__3.svg" alt="Deploy with Diploi" style="height: 40px;"></center>
</a>
</div>
<hr>
<h2>✨ Features</h2>
<ul>
<li><strong>👤 User Onboarding:</strong> A guided setup process to collect a user's name, gender, age, and location.</li>
<li><strong>💬 Anonymous Human Chat:</strong> Connects two random users for a one-on-one, privacy-focused conversation.</li>
<li><strong>⚤ Gender-Based Pairing:</strong> Allows users to find a chat partner of a specific gender.</li>
<li><strong>🤖 Advanced AI Assistant ("Lisa"):</strong> Chat directly with Lisa, a friendly AI partner with a distinct personality. This AI is powered by a hybrid model using Ollama for core conversation and Groq for specialized tasks.</li>
<li><strong>🛠️ AI with Tools:</strong>
<ul>
<li><strong>🌐 Real-time Web Search:</strong> Lisa can perform text searches using the Google Custom Search API to fetch real-time information, news, scores, and facts.</li>
<li><strong>🖼️ Image Search:</strong> Lisa can find and send images when a user explicitly asks for a picture.</li>
<li><strong>🧠 Long-term Memory:</strong> Lisa can remember key facts about you across conversations to create a more personalized experience.</li>
<li><strong>🎤 Voice & Vision:</strong> Processes voice notes and analyzes images sent by the user, powered by Groq's fast transcription and vision models.</li>
</ul>
</li>
<li><strong>🔐 Privacy Focused:</strong> Forwards messages without revealing user identities and protects content from being forwarded or saved.</li>
<li><strong>👑 Admin Panel:</strong> Special commands for the bot admin to view usage statistics and broadcast messages to all users.</li>
<li><strong>🚀 Robust & Asynchronous:</strong> Built with <code>asyncio</code> to handle many conversations concurrently without blocking.</li>
<li><strong>❤️ Health Check:</strong> Includes a <code>run.py</code> with a web server to provide a health check endpoint, perfect for modern hosting platforms like Diploi, Render, or Heroku.</li>
</ul>
<hr>
<h2>🛠️ Project Structure</h2>
<p>The bot is organized into several key files:</p>
<pre><code style="background-color: #f1f1f1; display: block; padding: 10px;">/your-project
├── memory/
├── voice_notes/
├── Dockerfile
├── requirements.txt
├── bot.py
├── run.py
├── db_connection.py
└── UserStatus.py
</code></pre>
<ul>
<li><code>bot.py</code>: The main application logic, containing all handlers and the bot's core functionality.</li>
<li><code>run.py</code>: The entry point for production deployment. It starts a simple web server (e.g., Flask) to respond to health checks and then runs the main bot process from <code>bot.py</code>.</li>
<li><code>db_connection.py</code>: Manages all interactions with the SQLite database for user profiles and chat pairing.</li>
<li><code>UserStatus.py</code>: Contains the <code>Enum</code> for managing user states (e.g., IDLE, IN_SEARCH, COUPLED).</li>
<li><code>Dockerfile</code>: Instructions to build the container image for easy deployment.</li>
<li><code>requirements.txt</code>: Lists all the Python packages required to run the bot.</li>
<li><code>memory/</code> & <code>voice_notes/</code>: Directories for storing user memory and temporary media files.</li>
</ul>
<hr>
<h2>🚀 Deployment</h2>
<p>You can run this bot either inside a Docker container (recommended for production) or directly on your local machine for development and testing.</p>
<h3><strong>🐳 How to Run Using Docker (Production)</strong></h3>
<p>Docker is the recommended way to run this bot in production for consistency and ease of management. Platforms like Diploi can build and run the container for you automatically.</p>
<h4><strong>1. Build the Docker Image</strong></h4>
<p>From the root directory of the project, run the following command:</p>
<pre><code style="background-color: #f1f1f1; display: block; padding: 10px;">docker build -t telegram-chat-bot .</code></pre>
<h4><strong>2. Run the Docker Container</strong></h4>
<p>Run the container by providing your credentials as environment variables. This is the most secure method.</p>
<pre><code style="background-color: #f1f1f1; display: block; padding: 10px;">docker run -d --name my-chat-bot \
-e BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN" \
-e ADMIN_ID="YOUR_TELEGRAM_ADMIN_ID" \
-e BOT_OWNER_CONTACT="@YourSupportUsername" \
-e OLLAMA_API_KEY="YOUR_OLLAMA_API_KEY" \
-e GROQ_API_KEY="YOUR_GROQ_API_KEY" \
-e GOOGLE_API_KEY="YOUR_GOOGLE_CLOUD_API_KEY" \
-e GOOGLE_CSE_ID="YOUR_GOOGLE_CSE_ID" \
-p 8000:8000 \
telegram-chat-bot
</code></pre>
<p>Your bot is now running in the background, and the health check server is accessible on port 8000!</p>
<h3><strong>💻 How to Run Locally (for Development)</strong></h3>
<p>Follow these steps to run the bot on your own machine. This is ideal for testing and development.</p>
<h4><strong>1. Create a Virtual Environment</strong></h4>
<p>It's a best practice to isolate your project's dependencies:</p>
<pre><code style="background-color: #f1f1f1; display: block; padding: 10px;"># Create the virtual environment
python3 -m venv venv
Activate it (on MacOS/Linux)
source venv/bin/activate
</code></pre>
<h4><strong>2. Install Dependencies</strong></h4>
<p>Install all the required Python libraries from the <code>requirements.txt</code> file. Ensure it includes a web server like Flask.</p>
<pre><code style="background-color: #f1f1f1; display: block; padding: 10px;">pip install -r requirements.txt
</code></pre>
<h4><strong>3. Configure Credentials</strong></h4>
<p>Before running, you must replace the placeholder values inside the <code>bot.py</code> script with your actual API keys and tokens.</p>
<h4><strong>4. Run the Bot</strong></h4>
<p>With your virtual environment active and credentials set, use <code>run.py</code> to start both the web server and the bot:</p>
<pre><code style="background-color: #f1f1f1; display: block; padding: 10px;">python run.py
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
<td rowspan="4"><strong>Profile & General</strong></td>
<td><code>/start</code></td>
<td>Starts the bot and begins the profile creation process.</td>
</tr>
<tr>
<td><code>/my_profile</code></td>
<td>Displays your user profile information.</td>
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
<td rowspan="6"><strong>Human Chat</strong></td>
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
<td><code>/report</code></td>
<td>Anonymously reports your current chat partner to the admin.</td>
</tr>
<tr>
<td rowspan="2"><strong>AI Chat</strong></td>
<td><code>/aichat</code></td>
<td>Starts a conversation with Lisa, the AI assistant.</td>
</tr>
<tr>
<td><code>/exit_aichat</code></td>
<td>Ends your conversation with the AI.</td>
</tr>
<tr>
<td rowspan="3" style="background-color: #fffbe6;"><strong>Admin</strong></td>
<td style="background-color: #fffbe6;"><code>/stats</code></td>
<td style="background-color: #fffbe6;">(Admin Only) Displays bot usage statistics.</td>
</tr>
<tr>
<td style="background-color: #fffbe6;"><code>/broadcast &lt;msg&gt;</code></td>
<td style="background-color: #fffbe6;">(Admin Only) Sends a message to all users.</td>
</tr>
<tr>
<td style="background-color: #fffbe6;"><code>/silent_broadcast &lt;msg&gt;</code></td>
<td style="background-color: #fffbe6;">(Admin Only) Sends a silent message to all users.</td>
</tr>
</tbody>
</table>
<hr>
<p>© 2026 Amhar Nisfer Dev, Inc.</p>
</body>
</html>
