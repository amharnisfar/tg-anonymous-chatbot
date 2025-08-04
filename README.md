<!DOCTYPE html>
<html>
<body>
<h1>Advanced Telegram Chat Bot</h1>
<p>This is a sophisticated Telegram bot that connects users for anonymous chats, complete with gender-based pairing and a direct line to a generative AI assistant named Rosi. It features a full user onboarding process, admin-specific commands, and a robust architecture designed for scalability.</p>
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
<pre><code>/your-project
├── Dockerfile
├── requirements.txt
├── bot.py
├── UserStatus.py
└── db_connection.py</code></pre>
<ul>
<li><code>bot.py</code>: The main application logic, containing all handlers and the bot's core functionality.</li>
<li><code>db_connection.py</code>: Manages all interactions with the SQLite database.</li>
<li><code>UserStatus.py</code>: Contains the <code>Enum</code> for managing user states (e.g., IDLE, IN_SEARCH, COUPLED).</li>
<li><code>requirements.txt</code>: Lists all the Python packages required to run the bot.</li>
<li><code>Dockerfile</code>: Instructions to build the container image for deployment.</li>
</ul>
<hr>
<h2>🚀 How to Run Using Docker</h2>
<p>Docker is the recommended way to run this bot in production.</p>
<h3><strong>1. Build the Docker Image</strong></h3>
<p>From the root directory of the project, run the following command:</p>
<pre><code>docker build -t telegram-chat-bot .</code></pre>
<h3><strong>2. Run the Docker Container</strong></h3>
<p>Run the container by providing your credentials as environment variables. This is the most secure method.</p>
<pre><code>docker run -d --name my-chat-bot \
  -e BOT_TOKEN="YOUR_ACTUAL_BOT_TOKEN" \
  -e ADMIN_ID="YOUR_ACTUAL_ADMIN_ID" \
  -e BOT_OWNER_CONTACT="@YourAdminUsername" \
  -e GOOGLE_AI_API_KEY="YOUR_ACTUAL_GOOGLE_AI_KEY" \
  -p 8080:8080 \
  telegram-chat-bot</code></pre>
<p>Your bot is now running in the background!</p>
<hr>
<h2>🤖 Bot Commands</h2>
<p>Here is a list of all available commands within the bot.</p>
<table border="1" style="width:100%; border-collapse: collapse;">
<thead>
<tr>
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
</tbody>
</table>
<hr>
<p>© 2025 Amhar Nisfer Dev, Inc.</p>
</body>
</html>
