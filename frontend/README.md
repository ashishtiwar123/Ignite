# Remix of Response Command Center

Use this prompt:

Build a hackathon-ready web app for an Emergency Disaster Response System with only two routes: / and /dashboard.
The UI should be clean, functional, and easy to demo in a 48-hour hackathon.

Route 1: /

This should be a simple landing/input screen. It should contain only the essential form inputs required to simulate a disaster scenario. The backend will provide or prefill the data, so the form should stay minimal and practical. Include fields like:

disaster type

location / zone

severity level

affected population

required resources

optional notes or description

There should be a single Submit / Start Simulation button. Once submitted, the app should route to /dashboard.

Route 2: /dashboard

This is the main command-center screen. It should feel like a real disaster operations dashboard, not a generic admin panel. The layout should include:

a collapsible left sidebar so the center map gets maximum space

a large central map area

a right panel for AI recommendations, live updates, and incident details

a bottom feed / timeline for events and actions

Map behavior

Use Mapbox satellite view only as the base map.
Do not use 3D buildings or a 3D basemap. The entire experience should be based on a high-quality satellite map that looks realistic and lively.

Disaster visualization

The map should clearly show:

disaster zones

affected regions

resource deployment areas

routes showing how help is reaching the location

shelters / hospitals / warehouses

incident markers

AI priority regions

The disaster overlays should look accurate and readable.
For example:

flood areas should appear as water regions / overlays

fire should appear as fire zones or heat regions

earthquake should appear as epicenter + impact circles

heavy rain should appear as rainfall / radar overlay

cyclone should appear as path / cone / storm overlay

Help and resource display

You do not need animated trucks moving in real time. It is enough to show:

which route the help is coming through

which resources are assigned

which zone is receiving help

ETA or status of deployed support

The map should show resource allocation correctly and make the flow of aid visually understandable.

Frontend requirements

Use the right kind of libraries for this kind of app, especially:

Mapbox

GSAP for smooth UI transitions and motion

any necessary map overlay / visualization utilities

Do not use Three.js or 3D rendering. This should remain a satellite-view-first dashboard.

Important behavior

Only two routes should exist: / and /dashboard

The home screen should stay simple

The dashboard should contain all live visualization and simulation behavior

The left sidebar must be collapsible

The map settings should allow a polished satellite-first experience

The UI should be lively, readable, and demo-friendly

Focus on clarity, realism, and effective disaster coordination visualization rather than unnecessary complexity

Goal

Create a visually strong and functional disaster response dashboard where the user can:

enter or receive disaster details,

start the simulation,

view the disaster on a satellite map,

see how resources are allocated,

understand the affected area clearly,

and follow the response flow at a glance.

For your reference I have given which is how ideally it should look like You cannot show blood like the water surf but it's fine the better you could show it is good that's it and make sure these things are developed in layers so that whenever I try to work with them I will be able to justified work on each layer correctly

## ResQAI Disaster Response System

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
