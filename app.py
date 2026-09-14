
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="3D Thermal Power Plant Simulator", layout="wide")

st.title("🔥 3D Thermal Power Plant + Boiler Simulator")
st.caption("Interactive 3D learning model — click equipment, rotate/zoom the plant, and watch water, steam, air, flue gas and cooling-water flows.")

with st.sidebar:
    st.header("3D Simulation Controls")
    speed = st.slider("Flow animation speed", 0.1, 3.0, 1.0, 0.1)
    show_water = st.checkbox("Water / steam flow", True)
    show_gas = st.checkbox("Flue-gas flow", True)
    show_air = st.checkbox("Combustion-air flow", True)
    show_cooling = st.checkbox("Cooling-water flow", True)
    st.markdown("---")
    st.write("🖱️ Drag = rotate")
    st.write("🔍 Wheel = zoom")
    st.write("🖱️ Right drag = pan")
    st.write("👆 Click equipment = inspect")

html = r"""
<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
html,body{margin:0;height:100%;overflow:hidden;background:#10131a;font-family:Arial}
#info,#panel,#tools{position:absolute;z-index:5;color:white;background:rgba(0,0,0,.75);border-radius:9px}
#info{left:12px;top:12px;padding:10px 12px;max-width:390px}
#panel{right:12px;top:12px;width:310px;padding:14px;display:none}
#panel h3{margin:0 0 8px}.small{font-size:13px;line-height:1.4}
#tools{left:12px;bottom:12px;padding:6px}
button{border:0;border-radius:5px;padding:7px 10px;margin:2px;cursor:pointer}
</style></head><body>
<div id="info"><b style="font-size:18px">3D Plant Overview</b><div class="small">Click any component to learn its function. Use the camera buttons for boiler/turbine views.</div></div>
<div id="panel"><h3 id="pn"></h3><div id="pt" class="small"></div><br><div id="pf" class="small"></div></div>
<div id="tools"><button onclick="view('plant')">Plant</button><button onclick="view('boiler')">Boiler</button><button onclick="view('turbine')">Turbine</button><button onclick="view('cycle')">Cycle</button></div>
<script src="https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.160.0/examples/js/controls/OrbitControls.js"></script>
<script>
const scene=new THREE.Scene(); scene.background=new THREE.Color(0x10131a);
const camera=new THREE.PerspectiveCamera(45,innerWidth/innerHeight,.1,3000);
camera.position.set(42,30,52);
const renderer=new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2)); renderer.setSize(innerWidth,innerHeight);
document.body.appendChild(renderer.domElement);
const controls=new THREE.OrbitControls(camera,renderer.domElement);
controls.enableDamping=true; controls.target.set(0,10,0);
scene.add(new THREE.HemisphereLight(0xffffff,0x334455,2.2));
const dl=new THREE.DirectionalLight(0xffffff,2.3); dl.position.set(25,50,20); scene.add(dl);
scene.add(new THREE.GridHelper(120,30,0x444a55,0x252a33));
const equipment=[], flows=[];

function M(c){return new THREE.MeshStandardMaterial({color:c,metalness:.25,roughness:.5})}
function box(name,x,y,z,sx,sy,sz,c,fn,type){
 const g=new THREE.Group();g.position.set(x,y,z);g.userData={name,fn,type};
 g.add(new THREE.Mesh(new THREE.BoxGeometry(sx,sy,sz),M(c)));scene.add(g);equipment.push(g);return g;
}
function cyl(name,x,y,z,r,h,c,fn,type){
 const g=new THREE.Group();g.position.set(x,y,z);g.userData={name,fn,type};
 const m=new THREE.Mesh(new THREE.CylinderGeometry(r,r,h,32),M(c));m.rotation.z=Math.PI/2;g.add(m);
 scene.add(g);equipment.push(g);return g;
}
function pipe(a,b,c){
 const A=new THREE.Vector3(...a),B=new THREE.Vector3(...b),d=B.clone().sub(A);
 const m=new THREE.Mesh(new THREE.CylinderGeometry(.16,.16,d.length,12),M(c));
 m.position.copy(A.clone().add(B).multiplyScalar(.5));
 m.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),d.normalize());scene.add(m);
}
function label(t,p){
 const c=document.createElement('canvas');c.width=300;c.height=70;const x=c.getContext('2d');
 x.fillStyle='white';x.font='bold 26px Arial';x.fillText(t,5,40);
 const s=new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(c),transparent:true}));
 s.position.set(...p);s.scale.set(6,1.4,1);scene.add(s);
}

// BOILER AND HEAT RECOVERY
box("Boiler Furnace / Waterwalls",-20,13,0,13,25,12,0x633025,"Fuel burns in the furnace. Waterwall tubes absorb radiant and convective heat and generate steam.","Boiler");
cyl("Steam Drum",-20,27,0,2.4,12,0x4d709c,"Separates steam from water and provides boiler inventory.","Boiler");
box("Economizer",-12,9,-1,6,9,7,0x66818c,"Recovers flue-gas heat and raises feedwater temperature.","Heat recovery");
box("Superheater",-12,20,0,5,7,8,0x98602d,"Raises saturated steam temperature above saturation.","Boiler");
box("Reheater",-3,18,0,6,7,8,0xa56f31,"Reheats HP turbine exhaust before IP expansion.","Boiler");
box("Air Preheater",2,8,-4,7,8,7,0x696157,"Transfers heat from flue gas to combustion air.","Heat recovery");
box("ESP / Dust Collector",10,8,-3,6,8,7,0x4c5868,"Removes particulate matter from flue gas.","Emission control");
cyl("Stack / Chimney",18,17,-3,2.2,20,0x777777,"Discharges treated flue gas.","Flue gas");

// FUEL / AIR
box("Coal Mill / Fuel Preparation",-34,7,5,6,7,6,0x555d68,"Pulverizes or conditions fuel before furnace entry.","Fuel system");
box("Fuel Feeder / Hopper",-34,14,5,6,5,6,0x705438,"Meters fuel to the furnace.","Fuel system");
cyl("FD Fan",0,5,10,2.2,4,0x3f815e,"Supplies combustion air to the furnace.","Fan");
cyl("PA Fan",-8,5,10,2,4,0x3f815e,"Primary air transports/pulverizes fuel in coal-fired systems.","Fan");
cyl("ID Fan",14,5,6,2.2,4,0x3f815e,"Draws flue gas through the boiler and maintains furnace draft.","Fan");

// TURBINE / GENERATOR
cyl("HP Turbine",8,16,7,2.8,9,0xa2a6ad,"First expansion of high-pressure main steam.","Turbine");
cyl("IP Turbine",18,16,7,2.6,8,0xa2a6ad,"Intermediate-pressure expansion after reheating.","Turbine");
cyl("LP Turbine",28,16,7,3.5,10,0xa2a6ad,"Final expansion toward condenser pressure.","Turbine");
cyl("Generator",36,15,7,3,9,0xb28f55,"Converts turbine shaft power into electrical power.","Electrical");

// CONDENSATE / FEEDWATER / COOLING
box("Surface Condenser",30,7,0,12,7,10,0x416f80,"Condenses LP exhaust steam and maintains low turbine back pressure.","Condenser");
cyl("Condensate Pump",22,3,0,1.4,4,0x397e98,"Moves condensate from condenser toward feedwater equipment.","Pump");
box("Deaerator",10,3,0,8,4,5,0x588493,"Removes dissolved gases and heats feedwater.","Feedwater");
cyl("Boiler Feed Pump",-1,3,0,1.7,5,0x397e98,"Raises feedwater pressure to boiler pressure.","Pump");
box("Cooling Tower",34,3,-13,9,13,9,0x3f6f79,"Rejects condenser heat to atmosphere.","Cooling");
box("Ash Handling",-30,4,-12,10,5,7,0x51473e,"Collects and transports ash.","Balance of plant");
box("Boiler Blowdown",-24,5,10,5,4,4,0x73514a,"Removes concentrated dissolved solids from boiler water.","Water treatment");

// PIPING
pipe([22,7,0],[22,4,0],0x45b8ff);pipe([20,3,0],[14,3,0],0x45b8ff);
pipe([6,3,0],[1,3,0],0x45b8ff);pipe([0,4,0],[-8,8,0],0x45b8ff);
pipe([-8,13,0],[-16,25,0],0x45b8ff);pipe([-14,27,0],[-12,22,0],0x45b8ff);
pipe([-7,22,0],[5,16,7],0x45b8ff);pipe([11,16,7],[14,16,7],0x45b8ff);
pipe([22,16,7],[24,16,7],0x45b8ff);pipe([33,16,7],[30,10,0],0x45b8ff);
pipe([-20,20,-6],[-12,12,-4],0xe77a36);pipe([-9,10,-4],[-1,9,-4],0xe77a36);
pipe([5,9,-4],[9,9,-3],0xe77a36);pipe([13,9,-3],[17,16,-3],0xe77a36);
pipe([2,7,10],[-10,9,5],0x61df8c);pipe([-8,7,10],[-25,12,5],0x61df8c);
pipe([30,5,0],[28,5,-8],0x31d4d4);pipe([28,5,-8],[34,5,-13],0x31d4d4);

// INTERNAL BOILER TUBES / DOWNCOMERS
for(let i=0;i<7;i++) cyl("Waterwall Tube",-25+i*1.6,14,6.15,.12,19,0x5db4dc,"Evaporator tube carrying water/steam mixture.","Boiler tube","z");
for(let i=0;i<5;i++) cyl("Drum Downcomer",-24+i*2,18,-6.1,.16,16,0x4b8fb0,"Returns water from the drum to the lower waterwalls.","Boiler tube","z");

// PARTICLE FLOWS
function particle(color){const m=new THREE.Mesh(new THREE.SphereGeometry(.32,10,10),new THREE.MeshBasicMaterial({color}));scene.add(m);return m}
function makeFlow(points,color,n){
 const p=points.map(a=>new THREE.Vector3(...a)),arr=[];
 for(let i=0;i<n;i++)arr.push({m:particle(color),t:i/n,p});
 flows.push(arr);
}
function at(points,t){
 const u=Math.min(.999999,t)*(points.length-1),i=Math.floor(u),f=u-i;
 return points[i].clone().lerp(points[Math.min(i+1,points.length-1)],f);
}
const wp=[[22,7,0],[22,4,0],[14,3,0],[1,3,0],[-8,8,0],[-16,25,0],[-12,22,0],[-7,22,0],[5,16,7],[14,16,7],[24,16,7],[30,10,0]];
const gp=[[-20,20,-6],[-12,12,-4],[-1,9,-4],[9,9,-3],[17,16,-3]];
const ap=[[2,7,10],[-10,9,5],[-25,12,5]];
const cp=[[30,5,0],[28,5,-8],[34,5,-13],[36,7,-13],[30,7,0]];
makeFlow(wp,0x38aaff,35);makeFlow(gp,0xff782e,24);makeFlow(ap,0x5be18d,18);makeFlow(cp,0x32d3d3,20);

const enabled={water:__WATER__,gas:__GAS__,air:__AIR__,cool:__COOL__}, speed=__SPEED__;
function animate(){
 requestAnimationFrame(animate);const dt=.016;
 flows.forEach((arr,k)=>arr.forEach(o=>{o.t=(o.t+dt*.035*speed)%1;o.m.visible=[enabled.water,enabled.gas,enabled.air,enabled.cool][k];if(o.m.visible)o.m.position.copy(at(o.p,o.t));}));
 controls.update();renderer.render(scene,camera);
}
animate();

const ray=new THREE.Raycaster(),mouse=new THREE.Vector2();
renderer.domElement.addEventListener('click',e=>{
 mouse.x=e.clientX/innerWidth*2-1;mouse.y=-(e.clientY/innerHeight)*2+1;ray.setFromCamera(mouse,camera);
 const hit=ray.intersectObjects(equipment,true)[0];if(!hit)return;
 let g=hit.object;while(g.parent&&!g.userData.name)g=g.parent;
 if(g.userData.name){document.getElementById('pn').innerText=g.userData.name;document.getElementById('pt').innerText='Type: '+g.userData.type;document.getElementById('pf').innerText=g.userData.fn;document.getElementById('panel').style.display='block';}
});
function view(v){
 if(v==='plant'){camera.position.set(42,30,52);controls.target.set(0,10,0)}
 if(v==='boiler'){camera.position.set(-40,25,35);controls.target.set(-18,16,0)}
 if(v==='turbine'){camera.position.set(35,25,38);controls.target.set(22,16,7)}
 if(v==='cycle'){camera.position.set(0,45,58);controls.target.set(5,10,0)}
 controls.update();
}
addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight)});
</script></body></html>
"""

html = (html.replace("__WATER__", str(show_water).lower())
            .replace("__GAS__", str(show_gas).lower())
            .replace("__AIR__", str(show_air).lower())
            .replace("__COOL__", str(show_cooling).lower())
            .replace("__SPEED__", str(speed)))

components.html(html, height=790, scrolling=False)

st.markdown("### Component coverage")
st.write("Boiler/furnace • waterwalls • drum • downcomers • economizer • superheater • reheater • air preheater • ESP • stack • fuel feeder • coal mill • FD/PA/ID fans • HP/IP/LP turbines • generator • condenser • condensate pump • deaerator • boiler feed pump • cooling tower • ash handling • blowdown.")

st.warning("This is a schematic 3D training model, not manufacturer CAD. It is for understanding plant flow and component functions, not for equipment sizing, safety decisions or real plant operation.")
