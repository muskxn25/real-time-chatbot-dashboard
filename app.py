from flask import Flask
from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import redis
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
server = Flask(__name__)

# Initialize Redis for real-time data
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=0
)

# Initialize MongoDB for historical data
mongo_client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
db = mongo_client['chatbot_analytics']

# Initialize Dash app with dark theme
app = Dash(
    __name__,
    server=server,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True
)

# Layout
app.layout = dbc.Container([
    # Theme Toggle
    dbc.Row([
        dbc.Col([
            dbc.Switch(
                id="theme-toggle",
                label="Dark Mode",
                value=True,
                className="mb-4"
            )
        ], width=12)
    ]),
    
    # Header with animated title
    dbc.Row([
        dbc.Col([
            html.H1("🤖 AI Chatbot Analytics Dashboard", 
                   className="text-center my-4",
                   style={"animation": "pulse 2s infinite"})
        ], width=12)
    ]),
    
    # Real-time Stats Cards with animations
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📊 Total Messages", className="text-center"),
                dbc.CardBody([
                    html.H2(id="total-messages", children="0", 
                           className="text-center animate__animated animate__pulse animate__infinite"),
                    html.P("Last 24 hours", className="text-muted text-center")
                ])
            ], className="mb-4 shadow-lg animate__animated animate__fadeIn")
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("👥 Active Users", className="text-center"),
                dbc.CardBody([
                    html.H2(id="active-users", children="0", 
                           className="text-center animate__animated animate__pulse animate__infinite"),
                    html.P("Currently online", className="text-muted text-center")
                ])
            ], className="mb-4 shadow-lg animate__animated animate__fadeIn")
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("💰 API Cost", className="text-center"),
                dbc.CardBody([
                    html.H2(id="api-cost", children="$0.00", 
                           className="text-center animate__animated animate__pulse animate__infinite"),
                    html.P("Last 24 hours", className="text-muted text-center")
                ])
            ], className="mb-4 shadow-lg animate__animated animate__fadeIn")
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("⚡ Rate Limit Status", className="text-center"),
                dbc.CardBody([
                    html.H2(id="rate-limit", children="100%", 
                           className="text-center animate__animated animate__pulse animate__infinite"),
                    html.P("Remaining quota", className="text-muted text-center")
                ])
            ], className="mb-4 shadow-lg animate__animated animate__fadeIn")
        ], width=3)
    ]),
    
    # Enhanced Charts
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📈 Message Volume Over Time", className="text-center"),
                dbc.CardBody([
                    dcc.Graph(id='message-volume-chart',
                             config={'displayModeBar': False})
                ])
            ], className="mb-4 shadow-lg")
        ], width=12)
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("💵 API Cost Over Time", className="text-center"),
                dbc.CardBody([
                    dcc.Graph(id='cost-chart',
                             config={'displayModeBar': False})
                ])
            ], className="mb-4 shadow-lg")
        ], width=6),
        
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("⚡ Rate Limit Usage", className="text-center"),
                dbc.CardBody([
                    dcc.Graph(id='rate-limit-chart',
                             config={'displayModeBar': False})
                ])
            ], className="mb-4 shadow-lg")
        ], width=6)
    ]),
    
    # User Activity Heatmap
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🌡️ User Activity Heatmap", className="text-center"),
                dbc.CardBody([
                    dcc.Graph(id='activity-heatmap',
                             config={'displayModeBar': False})
                ])
            ], className="mb-4 shadow-lg")
        ], width=12)
    ]),
    
    # Update interval
    dcc.Interval(
        id='interval-component',
        interval=5*1000,  # in milliseconds
        n_intervals=0
    )
], fluid=True, className="p-4")

# Add custom CSS using app.css
app.css.append_css({
    'external_url': 'https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css'
})

# Callbacks
@app.callback(
    [Output('total-messages', 'children'),
     Output('active-users', 'children'),
     Output('api-cost', 'children'),
     Output('rate-limit', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_stats(n):
    # Get real-time stats from Redis
    total_messages = redis_client.get('total_messages') or 0
    active_users = redis_client.get('active_users') or 0
    api_cost = redis_client.get('api_cost') or 0
    rate_limit = redis_client.get('rate_limit') or 100
    
    return [
        f"{int(total_messages):,}",
        f"{int(active_users):,}",
        f"${float(api_cost):.2f}",
        f"{int(rate_limit)}%"
    ]

@app.callback(
    Output('message-volume-chart', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_message_volume(n):
    # Get historical data from MongoDB
    collection = db['message_logs']
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)
    
    pipeline = [
        {
            '$match': {
                'timestamp': {
                    '$gte': start_time,
                    '$lte': end_time
                }
            }
        },
        {
            '$group': {
                '_id': {
                    '$dateToString': {
                        'format': '%Y-%m-%d %H:00',
                        'date': '$timestamp'
                    }
                },
                'count': {'$sum': 1}
            }
        },
        {
            '$sort': {'_id': 1}
        }
    ]
    
    results = list(collection.aggregate(pipeline))
    
    # Create DataFrame
    df = pd.DataFrame(results)
    if not df.empty:
        df['_id'] = pd.to_datetime(df['_id'])
        df = df.set_index('_id')
    
    # Create figure with modern styling
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['count'],
        mode='lines+markers',
        name='Messages',
        line=dict(color='#00ff9d', width=3),
        marker=dict(size=8, color='#00ff9d'),
        fill='tozeroy',
        fillcolor='rgba(0, 255, 157, 0.1)'
    ))
    
    fig.update_layout(
        title='Message Volume Over Time',
        xaxis_title='Time',
        yaxis_title='Number of Messages',
        hovermode='x unified',
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        margin=dict(l=40, r=40, t=40, b=40)
    )
    
    return fig

@app.callback(
    Output('cost-chart', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_cost_chart(n):
    # Get cost data from MongoDB
    collection = db['api_costs']
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)
    
    results = list(collection.find({
        'timestamp': {
            '$gte': start_time,
            '$lte': end_time
        }
    }).sort('timestamp', 1))
    
    # Create DataFrame
    df = pd.DataFrame(results)
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
    
    # Create figure with modern styling
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['cost'],
        mode='lines+markers',
        name='API Cost',
        line=dict(color='#ff6b6b', width=3),
        marker=dict(size=8, color='#ff6b6b'),
        fill='tozeroy',
        fillcolor='rgba(255, 107, 107, 0.1)'
    ))
    
    fig.update_layout(
        title='API Cost Over Time',
        xaxis_title='Time',
        yaxis_title='Cost ($)',
        hovermode='x unified',
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        margin=dict(l=40, r=40, t=40, b=40)
    )
    
    return fig

@app.callback(
    Output('rate-limit-chart', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_rate_limit_chart(n):
    # Get rate limit data from MongoDB
    collection = db['rate_limits']
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)
    
    results = list(collection.find({
        'timestamp': {
            '$gte': start_time,
            '$lte': end_time
        }
    }).sort('timestamp', 1))
    
    # Create DataFrame
    df = pd.DataFrame(results)
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
    
    # Create figure with modern styling
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['remaining'],
        mode='lines+markers',
        name='Remaining Quota',
        line=dict(color='#4cc9f0', width=3),
        marker=dict(size=8, color='#4cc9f0'),
        fill='tozeroy',
        fillcolor='rgba(76, 201, 240, 0.1)'
    ))
    
    fig.update_layout(
        title='Rate Limit Usage',
        xaxis_title='Time',
        yaxis_title='Remaining Quota (%)',
        hovermode='x unified',
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        margin=dict(l=40, r=40, t=40, b=40)
    )
    
    return fig

@app.callback(
    Output('activity-heatmap', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_activity_heatmap(n):
    # Get user activity data from MongoDB
    collection = db['user_activity']
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)
    
    pipeline = [
        {
            '$match': {
                'timestamp': {
                    '$gte': start_time,
                    '$lte': end_time
                }
            }
        },
        {
            '$group': {
                '_id': {
                    'hour': {'$hour': '$timestamp'},
                    'day': {'$dayOfWeek': '$timestamp'}
                },
                'count': {'$sum': 1}
            }
        }
    ]
    
    results = list(collection.aggregate(pipeline))
    
    # Create DataFrame
    df = pd.DataFrame(results)
    if not df.empty:
        df['hour'] = df['_id'].apply(lambda x: x['hour'])
        df['day'] = df['_id'].apply(lambda x: x['day'])
        df = df.pivot(index='hour', columns='day', values='count')
        df = df.fillna(0)
    
    # Create heatmap with modern styling
    fig = go.Figure(data=go.Heatmap(
        z=df.values,
        x=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        y=[f"{h:02d}:00" for h in range(24)],
        colorscale='Viridis',
        showscale=True
    ))
    
    fig.update_layout(
        title='User Activity Heatmap',
        xaxis_title='Day of Week',
        yaxis_title='Hour of Day',
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        margin=dict(l=40, r=40, t=40, b=40)
    )
    
    return fig

if __name__ == '__main__':
    print("Dashboard is running at http://localhost:8051")
    app.run_server(debug=True, host='localhost', port=8051) 