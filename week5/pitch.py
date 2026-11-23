"""Accessible, dependency-free position picker using Streamlit Components v2."""
import streamlit as st

pitch = st.components.v2.component(
    "shot_pitch",
    html='''<svg class="pitch" viewBox="-4 -4 128 88" role="application" tabindex="0"
      aria-label="Shot position. Click the pitch or use arrow keys to move the shot.">
      <rect x="-4" y="-4" width="128" height="88" rx="3" fill="#123D34"/>
      <g fill="none" stroke="#A9C2B5" stroke-width=".35" pointer-events="none">
        <rect width="120" height="80"/><path d="M60 0V80"/>
        <circle cx="60" cy="40" r="9.15"/>
        <path d="M0 18H18V62H0 M120 18H102V62H120 M0 30H6V50H0 M120 30H114V50H120"/>
        <path d="M120 36H122V44H120" stroke="#F5F5EF" stroke-width=".8"/>
      </g>
      <polygon class="angle" fill="#D6F285" fill-opacity=".20" stroke="#D6F285" stroke-width=".35"/>
      <circle class="marker" r="1.6" fill="#D6F285" stroke="#123D34" stroke-width=".5"/>
      <text x="60" y="77" text-anchor="middle" fill="#D8E6DB" font-size="2.5">ATTACKING GOAL →</text>
    </svg>''',
    css='''.pitch{display:block;width:100%;height:auto;cursor:crosshair;touch-action:none;border-radius:12px}
    .pitch:focus-visible{outline:3px solid #618522;outline-offset:3px}
    text{font-family:Manrope,sans-serif}''',
    js='''export default function({parentElement,data,setTriggerValue}) {
      const svg=parentElement.querySelector('svg');
      let x=data.x,y=data.y;
      const draw=()=>{svg.querySelector('.marker').setAttribute('cx',x);
        svg.querySelector('.marker').setAttribute('cy',y);
        svg.querySelector('.angle').setAttribute('points',`${x},${y} 120,36 120,44`);
        svg.setAttribute('aria-label',`Shot at x ${x}, y ${y}. Click or use arrow keys.`);};
      const move=e=>{const p=svg.createSVGPoint();p.x=e.clientX;p.y=e.clientY;
        const q=p.matrixTransform(svg.getScreenCTM().inverse());
        x=Math.round(Math.max(0,Math.min(120,q.x))*10)/10;
        y=Math.round(Math.max(0,Math.min(80,q.y))*10)/10;draw();};
      svg.onpointerdown=e=>{svg.setPointerCapture(e.pointerId);move(e);};
      svg.onpointermove=e=>{if(svg.hasPointerCapture(e.pointerId))move(e);};
      svg.onpointerup=e=>{move(e);setTriggerValue('position',{x,y});};
      svg.onkeydown=e=>{const d={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]}[e.key];
        if(!d)return;e.preventDefault();x=Math.max(0,Math.min(120,x+d[0]));
        y=Math.max(0,Math.min(80,y+d[1]));draw();setTriggerValue('position',{x,y});};
      draw();
    }''',
)
