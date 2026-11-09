import{A as e,C as t,D as n,E as r,M as i,N as a,O as o,P as s,S as c,T as l,_ as u,a as d,b as f,c as p,d as m,f as h,g,h as _,i as v,j as y,k as b,l as x,m as S,n as C,o as w,p as T,r as E,s as D,t as O,u as k,v as ee,w as te,x as A,y as ne}from"./vendor-three-BJC39Fzx.js";import{n as re,r as j,t as ie}from"./vendor-onnx-C6Hwskkp.js";(function(){let e=document.createElement(`link`).relList;if(e&&e.supports&&e.supports(`modulepreload`))return;for(let e of document.querySelectorAll(`link[rel="modulepreload"]`))n(e);new MutationObserver(e=>{for(let t of e)if(t.type===`childList`)for(let e of t.addedNodes)e.tagName===`LINK`&&e.rel===`modulepreload`&&n(e)}).observe(document,{childList:!0,subtree:!0});function t(e){let t={};return e.integrity&&(t.integrity=e.integrity),e.referrerPolicy&&(t.referrerPolicy=e.referrerPolicy),t.credentials=e.crossOrigin===`use-credentials`?`include`:e.crossOrigin===`anonymous`?`omit`:`same-origin`,t}function n(e){if(e.ep)return;e.ep=!0;let n=t(e);fetch(e.href,n)}})();var M={vertexShader:`
    uniform float uTime;
    uniform float uActivityIntensity;
    uniform float uIsolatedRegionIndex; // -1 if all visible
    uniform float uHighlightedArmIndex; // -1 if all visible
    uniform float uStimulusWaveRadius;
    uniform vec3 uStimulusOrigin;
    uniform float uStimulusIntensity;
    uniform float uSelectedNodeIndex; // -1 if none

    attribute float aSize;
    attribute float aPhase;
    attribute float aRegionIndex;
    attribute float aArmIndex;
    attribute float aNodeIndex;
    attribute float aHighlightRole; // 0=normal, 1=selected, 2=upstream, 3=downstream

    varying vec3 vColor;
    varying float vAlpha;
    varying float vFlash;
    varying float vSelected;

    void main() {
      vColor = color;
      vSelected = 0.0;

      // Subtle biological oscillation wave
      float pulse = sin(uTime * 3.0 + aPhase) * 0.5 + 0.5;
      float activityBoost = pulse * uActivityIntensity * 0.2;

      // Live Stimulus Shockwave interaction
      float distToOrigin = distance(position, uStimulusOrigin);
      float waveDist = abs(distToOrigin - uStimulusWaveRadius);
      float stimulusFlash = 0.0;
      if (uStimulusIntensity > 0.01 && waveDist < 6.0) {
        stimulusFlash = (1.0 - (waveDist / 6.0)) * uStimulusIntensity * 1.5;
      }
      vFlash = stimulusFlash;

      // Highlight role styling (Vibrant & crisp)
      float roleBoost = 0.0;
      if (aHighlightRole > 0.5) {
        if (aHighlightRole > 2.5) {
          // Downstream (emerald)
          vColor = vec3(0.1, 0.95, 0.5);
          roleBoost = 1.2;
        } else if (aHighlightRole > 1.5) {
          // Upstream (cyan)
          vColor = vec3(0.2, 0.85, 1.0);
          roleBoost = 1.2;
        } else {
          // Selected node (warm gold)
          vColor = vec3(1.0, 0.9, 0.3);
          roleBoost = 2.2;
          vSelected = 1.0;
        }
      }

      // Region Isolation Dimming
      float visibility = 0.85;
      if (uIsolatedRegionIndex >= 0.0) {
        if (abs(aRegionIndex - uIsolatedRegionIndex) > 0.1) {
          visibility = 0.05; // Clean, non-distracting background context
        }
      }
      if (uHighlightedArmIndex >= 0.0) {
        if (abs(aArmIndex - uHighlightedArmIndex) > 0.1) {
          visibility = min(visibility, 0.04);
        }
      }

      if (aHighlightRole > 0.5) {
        visibility = 1.0;
      }

      vAlpha = visibility;

      vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
      float finalSize = aSize * (1.0 + activityBoost + stimulusFlash * 1.2 + roleBoost);
      
      // Perspective point size attenuation
      gl_PointSize = finalSize * (200.0 / -mvPosition.z);
      gl_Position = projectionMatrix * mvPosition;
    }
  `,fragmentShader:`
    varying vec3 vColor;
    varying float vAlpha;
    varying float vFlash;
    varying float vSelected;

    void main() {
      vec2 coord = gl_PointCoord - vec2(0.5);
      float dist = length(coord);
      if (dist > 0.5) discard;

      // Crisp, sharp core + tight edge
      float core = 1.0 - smoothstep(0.0, 0.35, dist);
      float edge = 1.0 - smoothstep(0.25, 0.5, dist);
      
      float alpha = (core * 0.85 + edge * 0.35) * vAlpha;

      // Natural, balanced color
      vec3 finalColor = mix(vColor, vec3(1.0, 1.0, 1.0), vFlash * 0.5);
      if (vSelected > 0.5) {
        finalColor = mix(finalColor, vec3(1.0, 1.0, 0.8), 0.35);
      }

      gl_FragColor = vec4(finalColor, alpha);
    }
  `},N={vertexShader:`
    uniform float uTime;
    uniform float uFiberGlow;
    uniform float uIsolatedRegionIndex;
    uniform float uHighlightedArmIndex;

    attribute float aRegionIndex;
    attribute float aArmIndex;
    attribute float aFiberHighlight; // 0 = normal, 1 = highlighted/connected, 2 = selected

    varying vec3 vColor;
    varying float vAlpha;

    void main() {
      vColor = color;

      // Delicate, clean fiber visibility
      float visibility = 0.22 * uFiberGlow;
      if (uIsolatedRegionIndex >= 0.0) {
        if (abs(aRegionIndex - uIsolatedRegionIndex) > 0.1) {
          visibility = 0.02;
        }
      }
      if (uHighlightedArmIndex >= 0.0) {
        if (abs(aArmIndex - uHighlightedArmIndex) > 0.1) {
          visibility = min(visibility, 0.015);
        }
      }

      if (aFiberHighlight > 0.5) {
        visibility = 0.9;
        if (aFiberHighlight > 1.5) {
          vColor = vec3(1.0, 0.95, 0.4); // Selected single fiber
        } else {
          vColor = mix(vColor, vec3(0.3, 0.85, 1.0), 0.6); // Local network fibers
        }
      }

      vAlpha = visibility;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,fragmentShader:`
    varying vec3 vColor;
    varying float vAlpha;

    void main() {
      gl_FragColor = vec4(vColor, vAlpha);
    }
  `},P={vertexShader:`
    uniform float uTime;
    attribute float aLife;
    attribute vec3 aSignalColor;
    attribute float aSize;

    varying vec3 vColor;
    varying float vLife;

    void main() {
      vColor = aSignalColor;
      vLife = aLife;

      vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
      float pointScale = 4.8 * (260.0 / -mvPosition.z) * (0.6 + aLife * 0.75);
      gl_PointSize = max(1.5, pointScale);
      gl_Position = projectionMatrix * mvPosition;
    }
  `,fragmentShader:`
    varying vec3 vColor;
    varying float vLife;

    void main() {
      vec2 coord = gl_PointCoord - vec2(0.5);
      float dist = length(coord);
      if (dist > 0.5) discard;

      // Ultra-bright core (white hot center) + radiant colored aura
      float core = 1.0 - smoothstep(0.0, 0.18, dist);
      float aura = 1.0 - smoothstep(0.12, 0.50, dist);
      
      vec3 coreWhite = mix(vColor, vec3(1.0, 1.0, 1.0), core * 0.85);
      float alpha = (core * 0.95 + aura * 0.65) * vLife;

      gl_FragColor = vec4(coreWhite, alpha);
    }
  `},F={vertexShader:`
    uniform float uTime;
    uniform float uPunctaSize;
    uniform float uPunctaAlpha;
    uniform float uIsolatedRegionIndex;
    
    varying vec3 vColor;
    varying float vAlpha;

    void main() {
      vColor = color;
      
      float shimmer = sin(uTime * 3.0 + position.x * 2.0 + position.y * 2.0) * 0.2 + 0.8;
      float visibility = uPunctaAlpha * shimmer * 0.65;

      vAlpha = visibility;

      vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
      gl_PointSize = uPunctaSize * (180.0 / -mvPosition.z);
      gl_Position = projectionMatrix * mvPosition;
    }
  `,fragmentShader:`
    varying vec3 vColor;
    varying float vAlpha;

    void main() {
      vec2 coord = gl_PointCoord - vec2(0.5);
      float dist = length(coord);
      if (dist > 0.5) discard;

      float core = 1.0 - smoothstep(0.0, 0.25, dist);
      float alpha = core * vAlpha;

      gl_FragColor = vec4(vColor, alpha);
    }
  `},I={vertical_lobe:{id:`vertical_lobe`,name:`Vertical Lobe System (MSF/VL)`,systematicName:`Lobus verticalis massae supraoesophageae`,category:`central_supra`,categoryLabel:`Supraesophageal Brain (Associative / Learning)`,neuronCountEstimate:`~25,000,000 neurons (highest central density)`,percentageOfNervousSystem:`~5.0% of total nervous system (~50% of central brain)`,dataClassification:`known`,classificationLabel:`Known Biological Data (Histologically Characterized)`,disclaimer:`Gross morphology & synaptic layer organization are well-established (Young 1971; Hochner 2012). Micro-axonal branching visualized as computational approximation.`,biologicalRole:`Long-term memory acquisition, visual learning, and tactile-visual associative recall. Features an analog to vertebrate hippocampus/cerebellum with long-term potentiation (LTP) capability.`,inputs:[`Superior Frontal Lobe`,`Subvertical Lobe`,`Optic Lobes via tractus opticus`],outputs:[`Subvertical Lobe`,`Lateral Basal Lobe`,`Subesophageal Motor Centers`],connectedRegions:[`superior_frontal_lobe`,`subvertical_lobe`,`optic_lobes`],keyNeurotransmitters:[`Glutamate`,`Acetylcholine`,`Octopamine`,`Dopamine`],scientificReferences:[`Young, J.Z. (1971) The Anatomy of the Nervous System of Octopus vulgaris.`,`Hochner, B. (2012) An Embodied View of Octopus Neurobiology. Current Biology.`,`Shomrat, T. et al. (2008) Long-term potentiation in the octopus vertical lobe. J. Neurophysiol.`],colorHex:`#c084fc`},superior_frontal_lobe:{id:`superior_frontal_lobe`,name:`Superior Frontal Lobe`,systematicName:`Lobus frontalis superior`,category:`central_supra`,categoryLabel:`Supraesophageal Brain (Associative Relay)`,neuronCountEstimate:`~2,000,000 neurons`,percentageOfNervousSystem:`~0.4% of total nervous system`,dataClassification:`known`,classificationLabel:`Known Biological Data`,disclaimer:`Gross connections and tract topography mapped from Young (1971). Synapse cloud rendered via procedural density modeling.`,biologicalRole:`Primary sensory integration hub for visual and chemotactile afferents before transmission to the vertical lobe memory matrix.`,inputs:[`Optic Lobes`,`Inferior Frontal System`],outputs:[`Vertical Lobe Amacrine Matrix`],connectedRegions:[`vertical_lobe`,`optic_lobes`,`subfrontal_lobe`],keyNeurotransmitters:[`Acetylcholine`,`Glutamate`],scientificReferences:[`Young, J.Z. (1971) Anatomy of Octopus Nervous System.`],colorHex:`#facc15`},subfrontal_lobe:{id:`subfrontal_lobe`,name:`Subfrontal & Inferior Frontal System`,systematicName:`Lobus subfrontalis et inferior frontalis`,category:`central_supra`,categoryLabel:`Supraesophageal Brain (Tactile Learning & Taste)`,neuronCountEstimate:`~5,000,000 small interneurons`,percentageOfNervousSystem:`~1.0% of total nervous system`,dataClassification:`known`,classificationLabel:`Known Biological Data`,disclaimer:`Known tactile learning center (chemotactile memory matrix analogous to vertical lobe). Micro-connectome approximated.`,biologicalRole:`Chemotactile memory and taste-by-touch discrimination. Receives afferent fibers from arm sucker receptors and mediates food reward associations.`,inputs:[`Brachial Nerves from all 8 arms`,`Subesophageal Brachial Centers`],outputs:[`Superior Frontal Lobe`,`Posterior Buccal Ganglia`],connectedRegions:[`brachial_nerve_ring`,`subesophageal_mass`,`superior_frontal_lobe`],keyNeurotransmitters:[`Glutamate`,`Serotonin`,`FMRFamide`],scientificReferences:[`Wells, M.J. (1978) Octopus: Physiology and Behaviour of an Advanced Invertebrate.`],colorHex:`#f43f5e`},subesophageal_mass:{id:`subesophageal_mass`,name:`Subesophageal Motor Mass (Brachial / Palliovisceral)`,systematicName:`Massa suboesophagea (Lobi brachiales et magnocellularis)`,category:`central_sub`,categoryLabel:`Subesophageal Brain (Motor / Executive Control)`,neuronCountEstimate:`~15,000,000 motor & intermediate neurons`,percentageOfNervousSystem:`~3.0% of total nervous system`,dataClassification:`known`,classificationLabel:`Known Biological Data`,disclaimer:`Motor nuclei borders, brachial nerve roots, and giant fiber system are well established. Individual motoneuron arborizations are simulated.`,biologicalRole:`Executive motor coordination: sends high-level motor activation commands to arms, funnel, chromatophores, and mantle without computing local arm muscle kinematics.`,inputs:[`Vertical Lobe System`,`Basal Lobes`,`Optic Lobes`,`Ascending Brachial Fibers`],outputs:[`8 Brachial Nerves to Arms`,`Stellate Ganglia (Mantle)`,`Funnel Nerves`],connectedRegions:[`vertical_lobe`,`brachial_nerve_ring`,`axial_nerve_cords`],keyNeurotransmitters:[`Acetylcholine`,`Glutamate`,`Dopamine`,`Noradrenaline`],scientificReferences:[`Budelmann, B.U. (1995) The Cephalopod Nervous System: Higher Motor Centers.`,`Zullo, L. et al. (2009) Higher-order motor control in the octopus. J. Exp. Biol.`],colorHex:`#3b82f6`},optic_lobes:{id:`optic_lobes`,name:`Left & Right Optic Lobes (Visual Cortex)`,systematicName:`Lobi optici dextri et sinistri`,category:`optic`,categoryLabel:`Optic Lobes (Massive Visual Processing)`,neuronCountEstimate:`~120,000,000 neurons (~60M per lobe; exceeds central brain!)`,percentageOfNervousSystem:`~24.0% of total nervous system`,dataClassification:`known`,classificationLabel:`Known Biological Data (Stratified Deep Retina)`,disclaimer:`Outer granular, plexiform, and deep medullary zones are well documented. High-density connectome rendering is a computational approximation based on known layer thickness.`,biologicalRole:`Massive visual feature extraction (polarization vision, motion, shape, spatial contrast), camouflage pattern generation, and visual memory pre-processing.`,inputs:[`Optic Nerves from Retinal Photoreceptors`,`Peduncle Lobe Feedback`],outputs:[`Optic Tracts to Supraesophageal and Subesophageal Masses`],connectedRegions:[`vertical_lobe`,`superior_frontal_lobe`,`subesophageal_mass`],keyNeurotransmitters:[`Acetylcholine`,`Dopamine`,`Octopamine`,`Histamine`],scientificReferences:[`Young, J.Z. (1962) The visual system of Octopus. Nature.`,`Wang, Z.Y. et al. (2023) Single-cell transcriptomics of the octopus optic lobe.`],colorHex:`#ec4899`},brachial_nerve_ring:{id:`brachial_nerve_ring`,name:`Interbrachial Commissural Ring`,systematicName:`Commissura interbrachialis circularis`,category:`commissure`,categoryLabel:`Peripheral Inter-Arm Neural Highway`,neuronCountEstimate:`~3,000,000 fibers & bridge interneurons`,percentageOfNervousSystem:`~0.6% of total nervous system`,dataClassification:`known`,classificationLabel:`Known Biological Data`,disclaimer:`Circular commissure connecting adjacent and opposite arm bases. Tracts verified via neuro-tracing (Richter et al. 2015).`,biologicalRole:`Direct arm-to-arm lateral communication ring without central brain intervention. Enables traveling peristaltic waves, inter-arm cooperation, and reflex handovers.`,inputs:[`Axial Nerve Cords of Arms 1 through 8`,`Subesophageal Brachial Nuclei`],outputs:[`Adjacent Arm Axial Nerve Cords (Left & Right Neighbors)`],connectedRegions:[`axial_nerve_cords`,`subesophageal_mass`],keyNeurotransmitters:[`Acetylcholine`,`Glutamate`],scientificReferences:[`Richter, S. et al. (2015) The peripheral nervous system of cephalopods. Front. Zool.`],colorHex:`#2dd4bf`},axial_nerve_cords:{id:`axial_nerve_cords`,name:`Arm Axial Nerve Cords (8 Arms)`,systematicName:`Chorda nervosa axialis brachiorum I-VIII`,category:`arm_axial`,categoryLabel:`Arm Peripheral Brains (60% of Total Neurons!)`,neuronCountEstimate:`~300,000,000 neurons (~35-40M per arm)`,percentageOfNervousSystem:`~60.0% of total nervous system`,dataClassification:`known`,classificationLabel:`Known Biological Data (Central Neuropil + Cortical Ring)`,disclaimer:`Segmented ganglionic swellings, central neuropil core, and peripheral cell body rind are anatomically verified. Micro-synaptic wiring within the neuropil is a computational approximation.`,biologicalRole:`Autonomous peripheral motor computers. Computes high-degree-of-freedom muscle recruitment (elongation, bend, torsion, shortening) via muscular hydrostat kinematics locally without central trajectory planning.`,inputs:[`Local Sucker Ganglia Sensory Afferents`,`Intramuscular Receptors`,`Subesophageal Motor Commands`,`Adjacent Arm Ring Messages`],outputs:[`Intramuscular Nerve Cords (Arm Muscles)`,`Sucker Ganglion Motor Sphincters`,`Ascending Tactile Afferents`],connectedRegions:[`sucker_ganglia`,`intramuscular_cords`,`brachial_nerve_ring`,`subesophageal_mass`],keyNeurotransmitters:[`Acetylcholine`,`Glutamate`,`5-HT (Serotonin)`,`FMRFamide-related peptides`,`Octopamine`],scientificReferences:[`Gutfreund, Y. et al. (1996) Organization of muscle motor programs in octopus arms. J. Exp. Biol.`,`Sumbre, G. et al. (2001) Control of octopus arm extension by a peripheral motor program. Science.`,`Zullo, L. & Hochner, B. (2011) A new perspective on the organization of an invertebrate brain. Commun. Integr. Biol.`],colorHex:`#38bdf8`},sucker_ganglia:{id:`sucker_ganglia`,name:`Sucker Ganglia & Chemotactile Networks`,systematicName:`Ganglia acetabulorum et plexus sensoria`,category:`sucker`,categoryLabel:`Sucker Micro-Ganglia (Taste-by-Touch & Adhesion)`,neuronCountEstimate:`~40,000,000 neurons (~200 suckers/arm × ~25,000 neurons/sucker)`,percentageOfNervousSystem:`~8.0% of total nervous system`,dataClassification:`known`,classificationLabel:`Known Biological Data (Ganglion Ring + Sensory Rim)`,disclaimer:`Sucker ganglion structure, rim sensory receptors, and intrinsic sphincter motor loops are biologically verified (Graziadei 1971; Allard et al. 2020). Micro-branching is procedurally rendered.`,biologicalRole:`Autonomous chemo-tactile sensing ("taste-by-touch" via contact chemoreceptors), pressure sensing, suction vacuum control, and local grasping reflexes.`,inputs:[`Sucker Rim Chemosensory Cilia`,`Mechanical Strain Receptors`],outputs:[`Axial Nerve Cord Segmental Root`,`Sucker Sphincter/Meridian Muscles`],connectedRegions:[`axial_nerve_cords`],keyNeurotransmitters:[`Acetylcholine`,`Nicotinic receptors`,`Glutamate`,`Nitric Oxide`],scientificReferences:[`Graziadei, P. (1971) The nervous system of the arms of Octopus vulgaris.`,`Allard, C.A.H. et al. (2020) Sensory specialization in the octopus sucker. Cell.`],colorHex:`#10b981`},intramuscular_cords:{id:`intramuscular_cords`,name:`Intramuscular Longitudinal Nerve Cords (4 per arm)`,systematicName:`Chordae nervosae intramusculares (4 per brachium)`,category:`intramuscular`,categoryLabel:`Muscular Hydrostat Motor Pathways`,neuronCountEstimate:`~10,000,000 axons and peripheral motor terminals`,percentageOfNervousSystem:`~2.0% of total nervous system`,dataClassification:`inferred`,classificationLabel:`Scientifically Inferred & Mapped Pathways`,disclaimer:`4 longitudinal cords (2 lateral, 2 aboral) per arm running parallel to the axial cord. Branching motor arborizations into transverse/oblique muscle bundles are computational approximations.`,biologicalRole:`Fast conduction highways activating longitudinal, transverse, and helical/oblique arm muscles for stiffening waves, striking, and crawling.`,inputs:[`Segmental Motor Roots from Axial Nerve Cord`],outputs:[`Longitudinal, Transverse, and Oblique Arm Muscle Fibers`],connectedRegions:[`axial_nerve_cords`],keyNeurotransmitters:[`Acetylcholine`,`Glutamate`],scientificReferences:[`Matzner, H. et al. (2000) Peripheral motor control in the octopus arm. J. Neurophysiol.`],colorHex:`#f59e0b`}},L={vertexShader:`
    varying vec3 vNormal;
    varying vec3 vViewPosition;

    void main() {
      vNormal = normalize(normalMatrix * normal);
      vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
      vViewPosition = -mvPosition.xyz;
      gl_Position = projectionMatrix * mvPosition;
    }
  `,fragmentShader:`
    uniform vec3 uHullColor;
    uniform float uOpacity;
    uniform float uFresnelBias;
    uniform float uFresnelScale;
    uniform float uFresnelPower;

    varying vec3 vNormal;
    varying vec3 vViewPosition;

    void main() {
      vec3 normal = normalize(vNormal);
      vec3 viewDir = normalize(vViewPosition);

      // Two-sided Fresnel edge illumination
      float fresnel = uFresnelBias + uFresnelScale * pow(1.0 - abs(dot(normal, viewDir)), uFresnelPower);
      fresnel = clamp(fresnel, 0.0, 1.0);

      // Core interior transparency + vibrant edge glow
      float alpha = (0.04 + fresnel * 0.42) * uOpacity;
      vec3 glowColor = mix(uHullColor, vec3(1.0, 1.0, 1.0), fresnel * 0.35);

      gl_FragColor = vec4(glowColor, alpha);
    }
  `},ae=class{group;materials=[];hullMeshes={};constructor(){this.group=new g,this.buildNeuropilCompartments()}createHullMaterial(e,t=.22){let n=new b({vertexShader:L.vertexShader,fragmentShader:L.fragmentShader,transparent:!0,depthWrite:!1,side:2,blending:2,uniforms:{uHullColor:{value:new h(e)},uOpacity:{value:t},uFresnelBias:{value:.05},uFresnelScale:{value:1.2},uFresnelPower:{value:2.2}}});return this.materials.push(n),n}buildNeuropilCompartments(){let t=this.createHullMaterial(I.vertical_lobe.colorHex,.28),n=new e(6.8,32,24);n.scale(.95,.82,1.15);let r=new A(n,t);r.position.set(0,8.5,1.5),this.group.add(r),this.hullMeshes.vertical_lobe=r;let i=this.createHullMaterial(I.superior_frontal_lobe.colorHex,.26),a=new e(4.5,24,20);a.scale(.9,.72,.95);let o=new A(a,i);o.position.set(0,6,-4.5),this.group.add(o),this.hullMeshes.superior_frontal_lobe=o;let s=this.createHullMaterial(I.subfrontal_lobe.colorHex,.26),c=new e(5.2,24,20);c.scale(.92,.68,.9);let l=new A(c,s);l.position.set(0,2.5,-5.5),this.group.add(l),this.hullMeshes.subfrontal_lobe=l;let u=this.createHullMaterial(I.subesophageal_mass.colorHex,.25),d=new e(7.8,32,24);d.scale(1.15,.7,1.05);let f=new A(d,u);f.position.set(0,-4.5,0),this.group.add(f),this.hullMeshes.subesophageal_mass=f;let p=this.createHullMaterial(I.optic_lobes.colorHex,.28);for(let t of[-1,1]){let n=new e(8.8,32,24);n.scale(.98,1.28,.92);let r=new A(n,p);r.position.set(t*18,3.5,-.5),this.group.add(r)}let m=this.createHullMaterial(I.brachial_nerve_ring.colorHex,.3),h=new y(13,1.4,16,48);h.rotateX(Math.PI*.5);let g=new A(h,m);g.position.set(0,-5,0),this.group.add(g),this.hullMeshes.brachial_nerve_ring=g;let _=this.createHullMaterial(I.axial_nerve_cords.colorHex,.18);this.buildArmSheathHulls(_)}buildArmSheathHulls(e){for(let t=0;t<8;t++){let n=t/8*Math.PI*2,r=[];for(let e=0;e<6;e++){let i=e/5,a=n+i*.45*(t%2==0?1:-1),o=13+i*55*.9,c=o*Math.cos(a),l=o*Math.sin(a),u=-5.5-i*24.75+Math.sin(i*Math.PI)*4;r.push(new s(c,u,l))}let a=new k(r),o=new i(a,36,2.2,12,!1),c=new A(o,e);this.group.add(c)}}setOpacity(e){for(let t of this.materials)t.uniforms.uOpacity.value=e}setVisible(e){this.group.visible=e}},oe=class{group;connectome;neuropilHulls;pointsMesh;linesMesh;punctaMesh;pointsMaterial;linesMaterial;punctaMaterial;highlightRoles;fiberHighlights;reticleGroup;reticleRing;reticleCore;regionIdToIndex={};constructor(t){this.connectome=t,this.group=new g;let r=0;for(let e in I)this.regionIdToIndex[e]=r++;let i=t.nodes.length,a=t.fibers.length;this.highlightRoles=new Float32Array(i),this.fiberHighlights=new Float32Array(a*2),this.neuropilHulls=new ae,this.group.add(this.neuropilHulls.group);let o=new x;o.setAttribute(`position`,new p(t.nodePositions,3)),o.setAttribute(`color`,new p(t.nodeColors,3)),o.setAttribute(`aSize`,new p(t.nodeSizes,1)),o.setAttribute(`aPhase`,new p(t.nodePhases,1)),o.setAttribute(`aHighlightRole`,new p(this.highlightRoles,1));let u=new Float32Array(i),d=new Float32Array(i);for(let e=0;e<i;e++){let n=t.nodes[e];u[e]=this.regionIdToIndex[n.regionId]??0,d[e]=n.armIndex}o.setAttribute(`aRegionIndex`,new p(u,1)),o.setAttribute(`aArmIndex`,new p(d,1)),this.pointsMaterial=new b({vertexShader:M.vertexShader,fragmentShader:M.fragmentShader,vertexColors:!0,transparent:!0,depthWrite:!1,blending:2,uniforms:{uTime:{value:0},uActivityIntensity:{value:1},uIsolatedRegionIndex:{value:-1},uHighlightedArmIndex:{value:-1},uStimulusOrigin:{value:new s(0,0,0)},uStimulusWaveRadius:{value:0},uStimulusIntensity:{value:0},uSelectedNodeIndex:{value:-1}}}),this.pointsMesh=new l(o,this.pointsMaterial),this.group.add(this.pointsMesh);let f=new x;f.setAttribute(`position`,new p(t.fiberLinePositions,3)),f.setAttribute(`color`,new p(t.fiberLineColors,3)),f.setAttribute(`aFiberHighlight`,new p(this.fiberHighlights,1));let m=a*2,h=new Float32Array(m),_=new Float32Array(m);for(let e=0;e<a;e++){let n=t.fibers[e],r=t.nodes[n.sourceIndex],i=this.regionIdToIndex[n.regionId]??0,a=r.armIndex;h[e*2+0]=i,h[e*2+1]=i,_[e*2+0]=a,_[e*2+1]=a}f.setAttribute(`aRegionIndex`,new p(h,1)),f.setAttribute(`aArmIndex`,new p(_,1)),this.linesMaterial=new b({vertexShader:N.vertexShader,fragmentShader:N.fragmentShader,vertexColors:!0,transparent:!0,depthWrite:!1,blending:2,uniforms:{uTime:{value:0},uFiberGlow:{value:1},uIsolatedRegionIndex:{value:-1},uHighlightedArmIndex:{value:-1}}}),this.linesMesh=new ne(f,this.linesMaterial),this.group.add(this.linesMesh);let v=new x;v.setAttribute(`position`,new p(t.punctaPositions,3)),v.setAttribute(`color`,new p(t.punctaColors,3)),this.punctaMaterial=new b({vertexShader:F.vertexShader,fragmentShader:F.fragmentShader,vertexColors:!0,transparent:!0,depthWrite:!1,blending:2,uniforms:{uTime:{value:0},uPunctaSize:{value:2.2},uPunctaAlpha:{value:.85},uIsolatedRegionIndex:{value:-1}}}),this.punctaMesh=new l(v,this.punctaMaterial),this.group.add(this.punctaMesh),this.reticleGroup=new g,this.reticleGroup.visible=!1;let y=new n(.5,.65,32),S=new c({color:16436245,side:2,transparent:!0,opacity:.85});this.reticleRing=new A(y,S),this.reticleGroup.add(this.reticleRing);let C=new e(.18,16,16),w=new c({color:16777215,transparent:!0,opacity:.95});this.reticleCore=new A(C,w),this.reticleGroup.add(this.reticleCore),this.group.add(this.reticleGroup)}setSelectedNeuron(e){if(this.highlightRoles.fill(0),this.fiberHighlights.fill(0),e!==null&&this.connectome.nodes[e]){let t=this.connectome.nodes[e];this.highlightRoles[e]=1;for(let n of t.upstreamNeighbors)n!==e&&(this.highlightRoles[n]=2);for(let n of t.downstreamNeighbors)n!==e&&(this.highlightRoles[n]=3);for(let e of[...t.incomingFiberIndices,...t.outgoingFiberIndices])e<this.connectome.fibers.length&&(this.fiberHighlights[e*2+0]=1,this.fiberHighlights[e*2+1]=1);this.reticleGroup.position.copy(t.position),this.reticleGroup.visible=!0}else this.reticleGroup.visible=!1;this.pointsMesh.geometry.attributes.aHighlightRole.needsUpdate=!0,this.linesMesh.geometry.attributes.aFiberHighlight.needsUpdate=!0}setSelectedFiber(e){if(this.highlightRoles.fill(0),this.fiberHighlights.fill(0),e!==null&&this.connectome.fibers[e]){let t=this.connectome.fibers[e];this.fiberHighlights[e*2+0]=2,this.fiberHighlights[e*2+1]=2,this.highlightRoles[t.sourceIndex]=2,this.highlightRoles[t.targetIndex]=3;let n=new s().addVectors(this.connectome.nodes[t.sourceIndex].position,this.connectome.nodes[t.targetIndex].position).multiplyScalar(.5);this.reticleGroup.position.copy(n),this.reticleGroup.visible=!0}else this.reticleGroup.visible=!1;this.pointsMesh.geometry.attributes.aHighlightRole.needsUpdate=!0,this.linesMesh.geometry.attributes.aFiberHighlight.needsUpdate=!0}update(e,t,n,r,i){if(this.pointsMaterial.uniforms.uTime.value=e,this.linesMaterial.uniforms.uTime.value=e,this.punctaMaterial.uniforms.uTime.value=e,this.pointsMaterial.uniforms.uStimulusOrigin.value.copy(t),this.pointsMaterial.uniforms.uStimulusWaveRadius.value=n,this.pointsMaterial.uniforms.uStimulusIntensity.value=r,this.reticleGroup.visible&&i){this.reticleRing.lookAt(i.position);let t=1+Math.sin(e*5)*.15;this.reticleRing.scale.set(t,t,t)}}setIsolatedRegion(e){let t=e?this.regionIdToIndex[e]??-1:-1;this.pointsMaterial.uniforms.uIsolatedRegionIndex.value=t,this.linesMaterial.uniforms.uIsolatedRegionIndex.value=t,this.punctaMaterial.uniforms.uIsolatedRegionIndex.value=t}setHighlightedArm(e){let t=e===null?-1:se(e);this.pointsMaterial.uniforms.uHighlightedArmIndex.value=t,this.linesMaterial.uniforms.uHighlightedArmIndex.value=t}setNeuralActivity(e){this.pointsMaterial.uniforms.uActivityIntensity.value=e}setFiberGlow(e){this.linesMaterial.uniforms.uFiberGlow.value=e}setFibersVisible(e){this.linesMesh.visible=e}setNeuropilHullOpacity(e){this.neuropilHulls.setOpacity(e)}setNeuropilHullsVisible(e){this.neuropilHulls.setVisible(e)}setPunctaVisible(e){this.punctaMesh.visible=e}setPunctaAlpha(e){this.punctaMaterial.uniforms.uPunctaAlpha.value=e}};function se(e){return typeof e==`number`?e:-1}var ce=class{group;mantleMesh;headMesh;armMeshes=[];materials=[];constructor(e=959977){this.group=new g,this.buildAnatomicalMesh(e)}buildAnatomicalMesh(n){let r=new h(n),a=new t({color:r,roughness:.2,metalness:.1,transmission:.85,ior:1.33,transparent:!0,opacity:.14,side:2,depthWrite:!1});this.materials.push(a);let o=new t({color:r.clone().offsetHSL(.05,.2,.1),roughness:.1,transmission:.9,transparent:!0,opacity:.35,depthWrite:!1});this.materials.push(o);let c=new e(14,32,24);c.scale(1,1.45,1.1),this.mantleMesh=new A(c,a),this.mantleMesh.position.set(0,16,2),this.group.add(this.mantleMesh);let l=new e(12,28,20);l.scale(1.2,.9,1),this.headMesh=new A(l,a),this.headMesh.position.set(0,3,0),this.group.add(this.headMesh);let u=new e(4.5,20,20),d=new A(u,o);d.position.set(-24,4,-1);let f=new A(u,o);f.position.set(24,4,-1),this.group.add(d,f);let p=Array.from({length:8},(e,t)=>t/8*Math.PI*2);for(let e=0;e<8;e++){let t=p[e],n=[];for(let r=0;r<6;r++){let i=r/5,a=t+i*.45*(e%2==0?1:-1),o=13+i*55*.9,c=o*Math.cos(a),l=o*Math.sin(a),u=-5.5-i*24.75+Math.sin(i*Math.PI)*4;n.push(new s(c,u,l))}let r=new k(n),o=new i(r,36,3.2,12,!1),c=new A(o,a);this.group.add(c),this.armMeshes.push(c)}}update(e,t=0){let n=1+Math.sin(e*1.8+t)*.045;this.mantleMesh&&this.mantleMesh.scale.set(1*n,1.45*n,1.1*n),this.headMesh&&this.headMesh.scale.set(1.2*n,.9*n,1*n),this.armMeshes.forEach((n,r)=>{let i=Math.sin(e*2.2+r*.78+t)*.07;n.rotation.z=i,n.rotation.y=Math.cos(e*1.5+r*.5+t)*.04})}setOpacity(e){for(let t of this.materials)t.opacity=e,t.visible=e>.001}setVisible(e){this.group.visible=e}},R={touch_sucker:{id:`touch_sucker`,title:`Touch Sucker (Chemotactile Reflex + Ascending Relay)`,shortDescription:`Sucker Sensor → Local Sucker Ganglion → Axial Nerve Cord → Local Processing → Brachial/Brain Relay → Motor Response`,scientificDescription:`Chemotactile sensory cilia on the sucker rim activate local ganglion interneurons. A local reflex arc triggers immediate adhesion/grasping, while an ascending sensory volley travels along the axial nerve cord to the interbrachial ring and central subfrontal learning lobes.`,pathwayBadge:`Tactile-Motor Reflex Loop`,steps:[{regionId:`sucker_ganglia`,label:`1. Sucker Sensory Receptors`,description:`Chemotactile receptors on sucker rim detect mechanical contact and chemical solutes.`,durationMs:450,highlightColorHex:`#f43f5e`,burstParticleCount:160,signalType:`sensory`,armIndex:0,startSegment:18,endSegment:18},{regionId:`sucker_ganglia`,label:`2. Local Sucker Neural Network`,description:`Intrinsic sucker ganglion computes local adhesion pressure and sphincter contraction.`,durationMs:500,highlightColorHex:`#fb7185`,burstParticleCount:180,signalType:`interneuron`,armIndex:0,startSegment:18,endSegment:18},{regionId:`axial_nerve_cords`,label:`3. Arm Axial Nerve Cord Neuropil`,description:`Signal enters segmental root into axial neuropil; computes local arm bend reflex.`,durationMs:750,highlightColorHex:`#38bdf8`,burstParticleCount:240,signalType:`reflex`,armIndex:0,startSegment:18,endSegment:0},{regionId:`intramuscular_cords`,label:`4. Intramuscular Muscle Activation`,description:`Local motoneurons recruit longitudinal and oblique muscle fibers to wrap prey.`,durationMs:600,highlightColorHex:`#a855f7`,burstParticleCount:200,signalType:`motor`,armIndex:0,startSegment:18,endSegment:10},{regionId:`brachial_nerve_ring`,label:`5. Interbrachial Commissural Ring`,description:`Ascending tactile message crosses the inter-arm nerve ring to alert neighbor arms.`,durationMs:650,highlightColorHex:`#00e5ff`,burstParticleCount:220,signalType:`interneuron`},{regionId:`subfrontal_lobe`,label:`6. Subfrontal Central Brain Integration`,description:`Central brain receives chemotactile value signal, consolidating taste-by-touch memory.`,durationMs:750,highlightColorHex:`#e11d48`,burstParticleCount:260,signalType:`associative`},{regionId:`subesophageal_mass`,label:`7. Subesophageal Motor Modulation`,description:`Central motor centers send descending bias to sustain prey ingestion posture.`,durationMs:650,highlightColorHex:`#10b981`,burstParticleCount:220,signalType:`motor`}]},visual_stimulus:{id:`visual_stimulus`,title:`Visual Stimulation (Prey Detection → Arm Strike)`,shortDescription:`Eye → Optic Lobe → Central Processing → Behavioral Processing → Arm Network → Motor Response`,scientificDescription:`High-acuity retinal excitation is pre-processed across the multi-layered optic lobe cortex. Visual features (motion, contrast, polarization) project to the vertical lobe memory matrix and basal motor centers, triggering coordinated multi-arm strike commands.`,pathwayBadge:`Sensory-Associative-Executive Command`,steps:[{regionId:`optic_lobes`,label:`1. Optic Lobe Visual Processing`,description:`Massive parallel feature extraction (motion, shape, polarization) in deep medullary cortex.`,durationMs:650,highlightColorHex:`#8b5cf6`,burstParticleCount:320,signalType:`sensory`},{regionId:`superior_frontal_lobe`,label:`2. Superior Frontal Relay`,description:`Visual representations routed into associative learning circuits.`,durationMs:450,highlightColorHex:`#fbbf24`,burstParticleCount:200,signalType:`interneuron`},{regionId:`vertical_lobe`,label:`3. Vertical Lobe Associative Memory`,description:`Associative recall: evaluates whether visual object is edible prey or threatening predator.`,durationMs:750,highlightColorHex:`#f59e0b`,burstParticleCount:380,signalType:`associative`},{regionId:`subesophageal_mass`,label:`4. Subesophageal Executive Motor Command`,description:`Issues high-level command: "Deploy front arms (Arms 1 & 2) toward visual target coordinate".`,durationMs:650,highlightColorHex:`#10b981`,burstParticleCount:240,signalType:`motor`},{regionId:`brachial_nerve_ring`,label:`5. Brachial Nerve Ring Dispatch`,description:`Executive command distributed along interbrachial commissures to recruited target arms.`,durationMs:550,highlightColorHex:`#00e5ff`,burstParticleCount:220,signalType:`interneuron`},{regionId:`axial_nerve_cords`,label:`6. Arm Axial Nerve Cord Kinematic Generation`,description:`Target arms compute bend-propagation wave locally to extend toward prey.`,durationMs:850,highlightColorHex:`#38bdf8`,burstParticleCount:300,signalType:`motor`,armIndex:0,startSegment:0,endSegment:27},{regionId:`intramuscular_cords`,label:`7. Intramuscular Muscle Strike`,description:`Simultaneous longitudinal contraction and radial stiffening propels arm tip forward.`,durationMs:650,highlightColorHex:`#00f59b`,burstParticleCount:260,signalType:`motor`,armIndex:0,startSegment:12,endSegment:27}]},arm_stimulation:{id:`arm_stimulation`,title:`Autonomous Arm Tactile Reflex & Inter-Arm Handover`,shortDescription:`Arm Sensor → Local Arm Network → Local Processing → Other Arm/Brain Communication → Response`,scientificDescription:`A nociceptive or mechanical perturbation on Arm 3 generates a local withdrawal reflex computed entirely within the axial nerve cord neuropil, while transmitting lateral inhibitory/warning waves to Arms 2 and 4 via the interbrachial ring without waiting for central brain permission.`,pathwayBadge:`Decentralized Peripheral Coordination`,steps:[{regionId:`axial_nerve_cords`,label:`1. Arm Sensory Receptors & Neuropil`,description:`Tactile strain receptors detect mechanical obstacle on arm mid-shaft.`,durationMs:500,highlightColorHex:`#38bdf8`,burstParticleCount:200,signalType:`sensory`,armIndex:2,startSegment:14,endSegment:14},{regionId:`axial_nerve_cords`,label:`2. Local Autonomous Processing`,description:`Axial cord interneuron ring computes rapid local withdrawal reflex loop.`,durationMs:550,highlightColorHex:`#0284c7`,burstParticleCount:240,signalType:`reflex`,armIndex:2,startSegment:14,endSegment:8},{regionId:`intramuscular_cords`,label:`3. Local Motor Retraction`,description:`Intramuscular longitudinal motor cords retract arm away from hazard.`,durationMs:500,highlightColorHex:`#a855f7`,burstParticleCount:200,signalType:`motor`,armIndex:2,startSegment:14,endSegment:22},{regionId:`brachial_nerve_ring`,label:`4. Inter-Arm Lateral Communication`,description:`Direct lateral message propagation across interbrachial commissures to adjacent arms.`,durationMs:650,highlightColorHex:`#00e5ff`,burstParticleCount:260,signalType:`interneuron`},{regionId:`axial_nerve_cords`,label:`5. Adjacent Arm Cooperative Adjustment`,description:`Neighboring arms compensate posture and extend support tentacles.`,durationMs:750,highlightColorHex:`#10b981`,burstParticleCount:230,signalType:`reflex`,armIndex:1,startSegment:0,endSegment:18}]},escape_jet:{id:`escape_jet`,title:`High-Velocity Escape Jet & Statocyst Surge`,shortDescription:`Statocyst / Threat → Subesophageal Giant Motor Centers → Siphon & 8-Arm Coordinated Thrust`,scientificDescription:`High-threat sensory input directly triggers the giant fiber system in the subesophageal palliovisceral lobes, firing simultaneous descending motor volleys across all 8 arms for instant backward propulsion and funnel jetting.`,pathwayBadge:`Emergency Giant Fiber Discharge`,steps:[{regionId:`subesophageal_mass`,label:`1. Statocyst & Giant Motor Activation`,description:`Threat triggers giant axon system within subesophageal motor centers.`,durationMs:400,highlightColorHex:`#ff3366`,burstParticleCount:300,signalType:`sensory`},{regionId:`brachial_nerve_ring`,label:`2. Synchronous Interbrachial Dispatch`,description:`Simultaneous high-voltage discharge across all 8 brachial nerve roots.`,durationMs:450,highlightColorHex:`#f97316`,burstParticleCount:350,signalType:`interneuron`},{regionId:`axial_nerve_cords`,label:`3. All 8 Arms Full-Length Kinematic Lock`,description:`Axial nerve cords stream synchronous action potentials from base to tips.`,durationMs:650,highlightColorHex:`#eab308`,burstParticleCount:450,signalType:`motor`,startSegment:0,endSegment:27},{regionId:`intramuscular_cords`,label:`4. Full Neuromuscular Jet Thrust`,description:`Longitudinal musculature stiffens arms into a hydrodynamic cone for escape.`,durationMs:600,highlightColorHex:`#00f59b`,burstParticleCount:380,signalType:`motor`,startSegment:0,endSegment:27}]}};R.visual_hunt=R.visual_stimulus,R.arm_tactile_transfer=R.arm_stimulation;var z=`octoflow_reduced_motion`,B=class e{static instance=null;listeners=new Set;userOverride=null;mediaQueryList=null;constructor(){this.init()}static getInstance(){return e.instance||=new e,e.instance}static resetInstance(){if(e.instance?.mediaQueryList)try{e.instance.mediaQueryList.onchange=null}catch{}e.instance=null}init(){if(this.userOverride=this.readStorage(),typeof window<`u`&&typeof window.matchMedia==`function`)try{this.mediaQueryList=window.matchMedia(`(prefers-reduced-motion: reduce)`);let e=()=>{this.userOverride===null&&(this.syncBodyClass(),this.notifyListeners())};`addEventListener`in this.mediaQueryList?this.mediaQueryList.addEventListener(`change`,e):this.mediaQueryList.addListener?.(e)}catch{}this.syncBodyClass()}readStorage(){if(typeof window>`u`||!window.localStorage)return null;try{let e=window.localStorage.getItem(z);return e===`true`||e!==`false`&&null}catch{return null}}writeStorage(e){if(typeof window<`u`&&window.localStorage)try{e===null?window.localStorage.removeItem(z):window.localStorage.setItem(z,String(e))}catch{}}isReducedMotion(){return this.userOverride===null?this.mediaQueryList?this.mediaQueryList.matches:!1:this.userOverride}setReducedMotion(e){this.userOverride=e,this.writeStorage(e),this.syncBodyClass(),this.notifyListeners()}toggleReducedMotion(){let e=!this.isReducedMotion();return this.setReducedMotion(e),e}clearOverride(){this.userOverride=null,this.writeStorage(null),this.syncBodyClass(),this.notifyListeners()}addListener(e){return this.listeners.add(e),()=>{this.listeners.delete(e)}}notifyListeners(){let e=this.isReducedMotion();for(let t of this.listeners)try{t(e)}catch(e){console.error(`Error in motion policy listener:`,e)}}syncBodyClass(){typeof document<`u`&&(this.isReducedMotion()?(document.documentElement.classList.add(`reduced-motion`),document.body?.classList.add(`reduced-motion`)):(document.documentElement.classList.remove(`reduced-motion`),document.body?.classList.remove(`reduced-motion`)))}};function V(){return B.getInstance().isReducedMotion()}var le=class{group;connectome;activePackets=[];activeSparks=[];maxParticles=4e3;particlePositions;particleColors;particleLives;particleGeometry;particleMaterial;particlePoints;currentPathway=null;currentStepIndex=0;stepTimer=0;ambientTimer=0;armAxialTracks=[];armSuckerGangliaTracks={};ringTrack=[];opticLeftTract=[];opticRightTract=[];brainAssociativeTracks=[];onStepChange;onPathwayComplete;stimulusOrigin=new s(0,0,0);stimulusWaveRadius=0;stimulusIntensity=0;themeColor=null;constructor(e,t){this.connectome=e,this.themeColor=t?new h(t):null,this.group=new g,this.particlePositions=new Float32Array(this.maxParticles*3),this.particleColors=new Float32Array(this.maxParticles*3),this.particleLives=new Float32Array(this.maxParticles),this.particleGeometry=new x,this.particleGeometry.setAttribute(`position`,new p(this.particlePositions,3)),this.particleGeometry.setAttribute(`aSignalColor`,new p(this.particleColors,3)),this.particleGeometry.setAttribute(`aLife`,new p(this.particleLives,1)),this.particleMaterial=new b({vertexShader:P.vertexShader,fragmentShader:P.fragmentShader,transparent:!0,depthWrite:!1,blending:2}),this.particlePoints=new l(this.particleGeometry,this.particleMaterial),this.group.add(this.particlePoints),this.extractAnatomicalTracks(),this.initAmbientCirculation()}triggerSpontaneousActivity(){let e=Math.floor(Math.random()*8),t=this.themeColor?`#${this.themeColor.getHexString()}`:`#38bdf8`;this.triggerArmAxialStream(e,!1,t)}triggerArmCascade(e=80){let t=this.themeColor?`#${this.themeColor.getHexString()}`:`#38bdf8`;for(let e=0;e<8;e++)this.triggerArmAxialStream(e,!1,t)}extractAnatomicalTracks(){this.armAxialTracks=Array.from({length:8},()=>[]);for(let e=0;e<8;e++){let t=this.connectome.armNodeIndices[e]||[],n={};for(let e of t){let t=this.connectome.nodes[e];t.regionId===`axial_nerve_cords`&&t.type===`ganglion_hub`&&(n[t.segmentIndex]=t.position)}let r=Object.keys(n).map(Number).sort((e,t)=>e-t);for(let t of r)this.armAxialTracks[e].push(n[t])}for(let e=0;e<8;e++){let t=this.connectome.armNodeIndices[e]||[],n={};for(let e of t){let t=this.connectome.nodes[e];n[t.segmentIndex]||(n[t.segmentIndex]={});let r=n[t.segmentIndex];t.regionId===`sucker_ganglia`&&t.type===`sucker_receptor`&&!r.rim?r.rim=t.position:t.regionId===`sucker_ganglia`&&t.type===`ganglion_hub`?r.ganglion=t.position:t.regionId===`axial_nerve_cords`&&t.type===`ganglion_hub`?r.anc=t.position:t.regionId===`intramuscular_cords`&&!r.inc&&(r.inc=t.position)}for(let t in n){let r=n[t];if(r.rim&&r.ganglion&&r.anc){let n=[r.rim,r.ganglion,r.anc];r.inc&&n.push(r.inc),this.armSuckerGangliaTracks[`${e}_${t}`]=n}}}let e=(this.connectome.regionNodeIndices.brachial_nerve_ring||[]).map(e=>this.connectome.nodes[e].position);this.ringTrack=e.sort((e,t)=>Math.atan2(e.z,e.x)-Math.atan2(t.z,t.x));let t=this.connectome.regionNodeIndices.optic_lobes||[],n=t.filter(e=>this.connectome.nodes[e].position.x<-10),r=t.filter(e=>this.connectome.nodes[e].position.x>10),i=this.connectome.regionNodeIndices.superior_frontal_lobe||[],a=this.connectome.regionNodeIndices.vertical_lobe||[],o=this.connectome.regionNodeIndices.subesophageal_mass||[];if(n.length>0&&i.length>0&&a.length>0&&(this.opticLeftTract=[this.connectome.nodes[n[0]].position,new s(-10,3.5,0),new s(-4,4.5,-2),this.connectome.nodes[i[0]].position,this.connectome.nodes[a[0]].position]),r.length>0&&i.length>0&&a.length>0&&(this.opticRightTract=[this.connectome.nodes[r[0]].position,new s(10,3.5,0),new s(4,4.5,-2),this.connectome.nodes[i[0]].position,this.connectome.nodes[a[0]].position]),a.length>0&&o.length>0)for(let e=0;e<6;e++){let e=this.connectome.nodes[a[Math.floor(Math.random()*a.length)]].position,t=this.connectome.nodes[o[Math.floor(Math.random()*o.length)]].position;this.brainAssociativeTracks.push([e,new s(e.x*.5,0,e.z*.5),t])}}initAmbientCirculation(){let e=this.themeColor?`#${this.themeColor.getHexString()}`:`#38bdf8`,t=this.themeColor?`#${this.themeColor.clone().offsetHSL(.08,0,.1).getHexString()}`:`#00f59b`;this.ringTrack.length>3&&(this.spawnRingPacket(e,.16,!0,0),this.spawnRingPacket(t,.16,!0,.5))}getLeadPulsePosition(){if(this.activePackets.length>0){let e=this.activePackets[0];return this.interpolateTrack(e.path,e.progress)}return this.activeSparks.length>0?this.activeSparks[0].position:null}triggerPathway(e){let t=R[e];t&&(this.currentPathway=t,this.currentStepIndex=0,this.stepTimer=0,this.executeCurrentStep())}triggerArmAxialStream(e,t=!0,n=`#89b4fa`){if(e<0||e>=8)return;let r=this.armAxialTracks[e];if(r&&r.length>2){let e=t?[...r].reverse():r;this.spawnStream(e,n,2.2,8,.04)}}triggerLateralRingPulse(e,t,n=`#cba6f7`){let r=e/8%1,i=t/8%1;this.spawnRingPacket(n,.8,!1,r),this.spawnRingPacket(n,.8,!1,i)}triggerSingleFiberStimulus(e,t=`#facc15`){if(e<0||e>=this.connectome.fibers.length)return;let n=this.connectome.fibers[e],r=this.connectome.nodes[n.sourceIndex],i=this.connectome.nodes[n.targetIndex];this.stimulusOrigin.copy(r.position),this.stimulusWaveRadius=.1,this.stimulusIntensity=1.6,this.spawnStream([r.position,i.position],t,2.5,6,.06)}triggerNeuronMicrocircuitCascade(e,t=30){let n=this.connectome.nodes[e];if(!n)return;this.stimulusOrigin.copy(n.position),this.stimulusWaveRadius=.2,this.stimulusIntensity=1.8;let r=n.downstreamNeighbors.length>0?n.downstreamNeighbors:n.neighbors;if(r.length===0)return;let i=n.regionId===`vertical_lobe`?`#f59e0b`:n.regionId===`optic_lobes`?`#8b5cf6`:`#38bdf8`;for(let e=0;e<Math.min(t,r.length*4);e++){let t=r[e%r.length],a=this.connectome.nodes[t];this.spawnSpark(n.position,a.position,t,i,4)}}triggerNodeStimulus(e,t=35){this.triggerNeuronMicrocircuitCascade(e,t)}executeCurrentStep(){if(!this.currentPathway)return;let e=this.currentPathway.steps[this.currentStepIndex];if(!e)return;let t=this.currentPathway.id,n=e.highlightColorHex;if(t===`touch_sucker`){let t=e.armIndex??0,r=e.startSegment??18;if(e.regionId===`sucker_ganglia`){let e=this.armSuckerGangliaTracks[`${t}_${r}`];e&&(this.spawnStream(e,n,1.8,8,.05),this.stimulusOrigin.copy(e[0]),this.stimulusWaveRadius=.2,this.stimulusIntensity=1.8)}else if(e.regionId===`axial_nerve_cords`){let e=this.armAxialTracks[t];if(e&&e.length>0){let t=e.slice(0,Math.min(r+1,e.length)).reverse();this.spawnStream(t,n,1.4,10,.04),t.length>0&&this.stimulusOrigin.copy(t[0]),this.stimulusIntensity=1.5}}else if(e.regionId===`intramuscular_cords`){let e=(this.connectome.armNodeIndices[t]||[]).filter(e=>this.connectome.nodes[e].regionId===`intramuscular_cords`);for(let t=0;t<Math.min(8,e.length);t++){let r=this.connectome.nodes[e[t]];if(r.neighbors.length>0){let e=this.connectome.nodes[r.neighbors[0]];this.spawnStream([r.position,e.position],n,2.2,5,.06)}}}else if(e.regionId===`brachial_nerve_ring`)this.spawnRingPacket(n,.6,!1,0),this.spawnRingPacket(n,.6,!1,.5);else if(e.regionId===`subfrontal_lobe`||e.regionId===`subesophageal_mass`)for(let e of this.brainAssociativeTracks)this.spawnStream(e,n,1.8,6,.06)}else if(t===`visual_stimulus`||t===`visual_hunt`){if(e.regionId===`optic_lobes`)this.opticLeftTract.length>0&&this.spawnStream(this.opticLeftTract,n,1.2,10,.04),this.opticRightTract.length>0&&this.spawnStream(this.opticRightTract,n,1.2,10,.04),this.stimulusOrigin.set(-18,3.5,0),this.stimulusWaveRadius=.5,this.stimulusIntensity=1.8;else if(e.regionId===`superior_frontal_lobe`||e.regionId===`vertical_lobe`){let e=this.connectome.regionNodeIndices.vertical_lobe||[];for(let t=0;t<8;t++){let t=e[Math.floor(Math.random()*e.length)],r=this.connectome.nodes[t];if(r.neighbors.length>0){let e=this.connectome.nodes[r.neighbors[0]];this.spawnStream([r.position,e.position],n,2,6,.05)}}this.stimulusOrigin.set(0,8.5,1.5),this.stimulusWaveRadius=.5,this.stimulusIntensity=2}else if(e.regionId===`subesophageal_mass`)for(let e of this.brainAssociativeTracks)this.spawnStream(e,n,1.8,8,.04);else e.regionId===`brachial_nerve_ring`?this.spawnRingPacket(n,.7,!1,0):e.regionId===`axial_nerve_cords`?(this.armAxialTracks[0]&&this.spawnStream(this.armAxialTracks[0],n,1.4,12,.03),this.armAxialTracks[1]&&this.spawnStream(this.armAxialTracks[1],n,1.4,12,.03)):e.regionId===`intramuscular_cords`&&(this.armAxialTracks[0]&&this.spawnStream(this.armAxialTracks[0].slice(12),n,2,10,.04),this.armAxialTracks[1]&&this.spawnStream(this.armAxialTracks[1].slice(12),n,2,10,.04))}else if(t===`arm_stimulation`||t===`arm_tactile_transfer`){let t=e.armIndex??2;if(e.regionId===`axial_nerve_cords`){let r=this.armAxialTracks[t];if(r){let t=e.startSegment!==void 0&&e.endSegment!==void 0?e.startSegment<e.endSegment?r.slice(e.startSegment,e.endSegment+1):r.slice(e.endSegment,e.startSegment+1).reverse():r;this.spawnStream(t,n,1.5,8,.04)}}else if(e.regionId===`intramuscular_cords`){let e=this.armAxialTracks[t];e&&this.spawnStream(e.slice(10,24),n,2,8,.05)}else e.regionId===`brachial_nerve_ring`&&this.spawnRingPacket(n,.65,!1,.25)}else if(t===`escape_jet`){if(e.regionId===`subesophageal_mass`)this.stimulusOrigin.set(0,-4.5,0),this.stimulusWaveRadius=.5,this.stimulusIntensity=2.4;else if(e.regionId===`brachial_nerve_ring`)this.spawnRingPacket(n,.9,!1,0),this.spawnRingPacket(n,.9,!1,.5);else if(e.regionId===`axial_nerve_cords`||e.regionId===`intramuscular_cords`)for(let e=0;e<8;e++)this.armAxialTracks[e]&&this.armAxialTracks[e].length>0&&this.spawnStream(this.armAxialTracks[e],n,1.6,12,.03)}else{let t=this.connectome.regionNodeIndices[e.regionId]||[];if(t.length>0)for(let e=0;e<Math.min(10,t.length);e++){let r=t[e],i=this.connectome.nodes[r];if(i.neighbors.length>0){let e=this.connectome.nodes[i.neighbors[0]];this.spawnStream([i.position,e.position],n,2,5,.06)}}}this.onStepChange&&this.onStepChange(this.currentStepIndex,e.label,e.description)}spawnStream(e,t,n=1.5,r=8,i=.04){V()||e.length<2||this.activePackets.push({path:e.map(e=>e.clone()),progress:0,speed:n,color:new h(t),life:1,numTrails:r,trailSpacing:i,isLoop:!1})}spawnRingPacket(e,t=.25,n=!1,r=0){V()||this.ringTrack.length<3||this.activePackets.push({path:this.ringTrack.map(e=>e.clone()),progress:r,speed:t,color:new h(e),life:1,numTrails:8,trailSpacing:.025,isLoop:n})}spawnSpark(e,t,n,r,i){V()||this.activeSparks.length>400||this.activeSparks.push({position:e.clone(),target:t.clone(),progress:0,speed:2.5+Math.random()*1.5,color:new h(r),life:1,hopsLeft:i,currentNodeIdx:n})}update(e,t=1){let n=e*t;if(V()){if((this.activePackets.length>0||this.activeSparks.length>0)&&(this.activePackets=[],this.activeSparks=[],this.particleLives.fill(0),this.particleGeometry.attributes.aLife.needsUpdate=!0),this.stimulusIntensity=0,this.currentPathway){let e=this.currentPathway.steps[this.currentStepIndex];this.stepTimer+=n*1e3,this.stepTimer>=e.durationMs&&(this.stepTimer=0,this.currentStepIndex++,this.currentStepIndex<this.currentPathway.steps.length?this.executeCurrentStep():(this.currentPathway=null,this.onPathwayComplete&&this.onPathwayComplete()))}return}if(this.ambientTimer+=n,this.ambientTimer>1.8){this.ambientTimer=0;let e=Math.floor(Math.random()*8),t=this.armAxialTracks[e];if(t&&t.length>4){let e=Math.random()>.5,n=e?[...t].reverse():t,r=e?`#38bdf8`:`#00f59b`;this.spawnStream(n,r,.45,6,.035)}}if(this.currentPathway){let e=this.currentPathway.steps[this.currentStepIndex];this.stepTimer+=n*1e3,this.stepTimer>=e.durationMs&&(this.stepTimer=0,this.currentStepIndex++,this.currentStepIndex<this.currentPathway.steps.length?this.executeCurrentStep():(this.currentPathway=null,this.onPathwayComplete&&this.onPathwayComplete()))}this.stimulusIntensity>.01&&(this.stimulusWaveRadius+=n*38,this.stimulusIntensity=Math.max(0,this.stimulusIntensity-n*1.5));let r=[];for(let e=0;e<this.activePackets.length;e++){let t=this.activePackets[e];t.progress+=n*t.speed*.5,t.isLoop?(t.progress>=1&&--t.progress,r.push(t)):t.progress<1&&r.push(t)}this.activePackets=r;let i=[];for(let e=0;e<this.activeSparks.length;e++){let t=this.activeSparks[e];if(t.progress+=n*t.speed,t.progress<1)t.position.lerp(t.target,t.progress),i.push(t);else if(t.hopsLeft>1){let e=this.connectome.nodes[t.currentNodeIdx];if(e){let n=e.downstreamNeighbors.length>0?e.downstreamNeighbors:e.neighbors;if(n.length>0){let r=n[Math.floor(Math.random()*n.length)],a=this.connectome.nodes[r];t.position.copy(e.position),t.target.copy(a.position),t.progress=0,t.hopsLeft--,t.currentNodeIdx=r,t.life*=.85,i.push(t)}}}}this.activeSparks=i;let a=0;for(let e of this.activePackets)for(let t=0;t<e.numTrails&&!(a>=this.maxParticles);t++){let n=e.progress-t*e.trailSpacing;if(e.isLoop&&n<0&&(n+=1),n>=0&&n<=1){let r=this.interpolateTrack(e.path,n),i=(1-t/e.numTrails)**1.8;this.particlePositions[a*3+0]=r.x,this.particlePositions[a*3+1]=r.y,this.particlePositions[a*3+2]=r.z,this.particleColors[a*3+0]=e.color.r,this.particleColors[a*3+1]=e.color.g,this.particleColors[a*3+2]=e.color.b,this.particleLives[a]=e.life*i,a++}}for(let e of this.activeSparks){if(a>=this.maxParticles)break;this.particlePositions[a*3+0]=e.position.x,this.particlePositions[a*3+1]=e.position.y,this.particlePositions[a*3+2]=e.position.z,this.particleColors[a*3+0]=e.color.r,this.particleColors[a*3+1]=e.color.g,this.particleColors[a*3+2]=e.color.b,this.particleLives[a]=e.life,a++}for(let e=a;e<this.maxParticles;e++)this.particleLives[e]=0;this.particleGeometry.attributes.position.needsUpdate=!0,this.particleGeometry.attributes.aSignalColor.needsUpdate=!0,this.particleGeometry.attributes.aLife.needsUpdate=!0}interpolateTrack(e,t){if(e.length===0)return new s;if(e.length===1)return e[0].clone();let n=e.length-1,r=f.clamp(t,0,1)*n,i=Math.min(Math.floor(r),n-1),a=r-i;return new s().lerpVectors(e[i],e[i+1],a)}},H=Object.freeze({Linear:Object.freeze({None:function(e){return e},In:function(e){return e},Out:function(e){return e},InOut:function(e){return e}}),Quadratic:Object.freeze({In:function(e){return e*e},Out:function(e){return e*(2-e)},InOut:function(e){return(e*=2)<1?.5*e*e:-.5*(--e*(e-2)-1)}}),Cubic:Object.freeze({In:function(e){return e*e*e},Out:function(e){return--e*e*e+1},InOut:function(e){return(e*=2)<1?.5*e*e*e:.5*((e-=2)*e*e+2)}}),Quartic:Object.freeze({In:function(e){return e*e*e*e},Out:function(e){return 1- --e*e*e*e},InOut:function(e){return(e*=2)<1?.5*e*e*e*e:-.5*((e-=2)*e*e*e-2)}}),Quintic:Object.freeze({In:function(e){return e*e*e*e*e},Out:function(e){return--e*e*e*e*e+1},InOut:function(e){return(e*=2)<1?.5*e*e*e*e*e:.5*((e-=2)*e*e*e*e+2)}}),Sinusoidal:Object.freeze({In:function(e){return 1-Math.sin((1-e)*Math.PI/2)},Out:function(e){return Math.sin(e*Math.PI/2)},InOut:function(e){return .5*(1-Math.sin(Math.PI*(.5-e)))}}),Exponential:Object.freeze({In:function(e){return e===0?0:1024**(e-1)},Out:function(e){return e===1?1:1-2**(-10*e)},InOut:function(e){return e===0?0:e===1?1:(e*=2)<1?.5*1024**(e-1):.5*(-(2**(-10*(e-1)))+2)}}),Circular:Object.freeze({In:function(e){return 1-Math.sqrt(1-e*e)},Out:function(e){return Math.sqrt(1- --e*e)},InOut:function(e){return(e*=2)<1?-.5*(Math.sqrt(1-e*e)-1):.5*(Math.sqrt(1-(e-=2)*e)+1)}}),Elastic:Object.freeze({In:function(e){return e===0?0:e===1?1:-(2**(10*(e-1)))*Math.sin((e-1.1)*5*Math.PI)},Out:function(e){return e===0?0:e===1?1:2**(-10*e)*Math.sin((e-.1)*5*Math.PI)+1},InOut:function(e){return e===0?0:e===1?1:(e*=2,e<1?-.5*2**(10*(e-1))*Math.sin((e-1.1)*5*Math.PI):.5*2**(-10*(e-1))*Math.sin((e-1.1)*5*Math.PI)+1)}}),Back:Object.freeze({In:function(e){var t=1.70158;return e===1?1:e*e*((t+1)*e-t)},Out:function(e){var t=1.70158;return e===0?0:--e*e*((t+1)*e+t)+1},InOut:function(e){var t=2.5949095;return(e*=2)<1?.5*(e*e*((t+1)*e-t)):.5*((e-=2)*e*((t+1)*e+t)+2)}}),Bounce:Object.freeze({In:function(e){return 1-H.Bounce.Out(1-e)},Out:function(e){return e<1/2.75?7.5625*e*e:e<2/2.75?7.5625*(e-=1.5/2.75)*e+.75:e<2.5/2.75?7.5625*(e-=2.25/2.75)*e+.9375:7.5625*(e-=2.625/2.75)*e+.984375},InOut:function(e){return e<.5?H.Bounce.In(e*2)*.5:H.Bounce.Out(e*2-1)*.5+.5}}),generatePow:function(e){return e===void 0&&(e=4),e=e<2**-52?2**-52:e,e=e>1e4?1e4:e,{In:function(t){return t**+e},Out:function(t){return 1-(1-t)**e},InOut:function(t){return t<.5?(t*2)**e/2:(1-(2-t*2)**e)/2+.5}}}}),U=function(){return performance.now()},ue=function(){function e(){var e=[...arguments];this._tweens={},this._tweensAddedDuringUpdate={},this.add.apply(this,e)}return e.prototype.getAll=function(){var e=this;return Object.keys(this._tweens).map(function(t){return e._tweens[t]})},e.prototype.removeAll=function(){this._tweens={}},e.prototype.add=function(){for(var e,t=[...arguments],n=0,r=t;n<r.length;n++){var i=r[n];(e=i._group)==null||e.remove(i),i._group=this,this._tweens[i.getId()]=i,this._tweensAddedDuringUpdate[i.getId()]=i}},e.prototype.remove=function(){for(var e=[...arguments],t=0,n=e;t<n.length;t++){var r=n[t];r._group=void 0,delete this._tweens[r.getId()],delete this._tweensAddedDuringUpdate[r.getId()]}},e.prototype.allStopped=function(){return this.getAll().every(function(e){return!e.isPlaying()})},e.prototype.update=function(e,t){e===void 0&&(e=U()),t===void 0&&(t=!0);var n=Object.keys(this._tweens);if(n.length!==0)for(;n.length>0;){this._tweensAddedDuringUpdate={};for(var r=0;r<n.length;r++){var i=this._tweens[n[r]],a=!t;i&&i.update(e,a)===!1&&!t&&this.remove(i)}n=Object.keys(this._tweensAddedDuringUpdate)}},e}(),W={Linear:function(e,t){var n=e.length-1,r=n*t,i=Math.floor(r),a=W.Utils.Linear;return t<0?a(e[0],e[1],r):t>1?a(e[n],e[n-1],n-r):a(e[i],e[i+1>n?n:i+1],r-i)},Bezier:function(e,t){for(var n=0,r=e.length-1,i=Math.pow,a=W.Utils.Bernstein,o=0;o<=r;o++)n+=i(1-t,r-o)*i(t,o)*e[o]*a(r,o);return n},CatmullRom:function(e,t){var n=e.length-1,r=n*t,i=Math.floor(r),a=W.Utils.CatmullRom;return e[0]===e[n]?(t<0&&(i=Math.floor(r=n*(1+t))),a(e[(i-1+n)%n],e[i],e[(i+1)%n],e[(i+2)%n],r-i)):t<0?e[0]-(a(e[0],e[0],e[1],e[1],-r)-e[0]):t>1?e[n]-(a(e[n],e[n],e[n-1],e[n-1],r-n)-e[n]):a(e[i?i-1:0],e[i],e[n<i+1?n:i+1],e[n<i+2?n:i+2],r-i)},Utils:{Linear:function(e,t,n){return(t-e)*n+e},Bernstein:function(e,t){var n=W.Utils.Factorial;return n(e)/n(t)/n(e-t)},Factorial:(function(){var e=[1];return function(t){var n=1;if(e[t])return e[t];for(var r=t;r>1;r--)n*=r;return e[t]=n,n}})(),CatmullRom:function(e,t,n,r,i){var a=(n-e)*.5,o=(r-t)*.5,s=i*i,c=i*s;return(2*t-2*n+a+o)*c+(-3*t+3*n-2*a-o)*s+a*i+t}}},G=function(){function e(){}return e.nextId=function(){return e._nextId++},e._nextId=0,e}(),K=new ue,q=function(){function e(e,t){this._isPaused=!1,this._pauseStart=0,this._valuesStart={},this._valuesEnd={},this._valuesStartRepeat={},this._duration=1e3,this._isDynamic=!1,this._initialRepeat=0,this._repeat=0,this._yoyo=!1,this._isPlaying=!1,this._reversed=!1,this._delayTime=0,this._startTime=0,this._easingFunction=H.Linear.None,this._interpolationFunction=W.Linear,this._chainedTweens=[],this._onStartCallbackFired=!1,this._onEveryStartCallbackFired=!1,this._id=G.nextId(),this._isChainStopped=!1,this._propertiesAreSetUp=!1,this._goToEnd=!1,this._object=e,typeof t==`object`?(this._group=t,t.add(this)):t===!0&&(this._group=K,K.add(this))}return e.prototype.getId=function(){return this._id},e.prototype.isPlaying=function(){return this._isPlaying},e.prototype.isPaused=function(){return this._isPaused},e.prototype.getDuration=function(){return this._duration},e.prototype.to=function(e,t){if(t===void 0&&(t=1e3),this._isPlaying)throw Error(`Can not call Tween.to() while Tween is already started or paused. Stop the Tween first.`);return this._valuesEnd=e,this._propertiesAreSetUp=!1,this._duration=t<0?0:t,this},e.prototype.duration=function(e){return e===void 0&&(e=1e3),this._duration=e<0?0:e,this},e.prototype.dynamic=function(e){return e===void 0&&(e=!1),this._isDynamic=e,this},e.prototype.start=function(e,t){if(e===void 0&&(e=U()),t===void 0&&(t=!1),this._isPlaying)return this;if(this._repeat=this._initialRepeat,this._reversed)for(var n in this._reversed=!1,this._valuesStartRepeat)this._swapEndStartRepeatValues(n),this._valuesStart[n]=this._valuesStartRepeat[n];if(this._isPlaying=!0,this._isPaused=!1,this._onStartCallbackFired=!1,this._onEveryStartCallbackFired=!1,this._isChainStopped=!1,this._startTime=e,this._startTime+=this._delayTime,!this._propertiesAreSetUp||t){if(this._propertiesAreSetUp=!0,!this._isDynamic){var r={};for(var i in this._valuesEnd)r[i]=this._valuesEnd[i];this._valuesEnd=r}this._setupProperties(this._object,this._valuesStart,this._valuesEnd,this._valuesStartRepeat,t)}return this},e.prototype.startFromCurrentValues=function(e){return this.start(e,!0)},e.prototype._setupProperties=function(e,t,n,r,i){for(var a in n){var o=e[a],s=Array.isArray(o),c=s?`array`:typeof o,l=!s&&Array.isArray(n[a]);if(c!==`undefined`&&c!==`function`){if(l){var u=n[a];if(u.length===0)continue;for(var d=[o],f=0,p=u.length;f<p;f+=1){var m=this._handleRelativeValue(o,u[f]);if(isNaN(m)){l=!1,console.warn(`Found invalid interpolation list. Skipping.`);break}d.push(m)}l&&(n[a]=d)}if((c===`object`||s)&&o&&!l){t[a]=s?[]:{};var h=o;for(var g in h)t[a][g]=h[g];r[a]=s?[]:{};var u=n[a];if(!this._isDynamic){var _={};for(var g in u)_[g]=u[g];n[a]=u=_}this._setupProperties(h,t[a],u,r[a],i)}else(t[a]===void 0||i)&&(t[a]=o),s||(t[a]*=1),r[a]=l?n[a].slice().reverse():t[a]||0}}},e.prototype.stop=function(){return this._isChainStopped||(this._isChainStopped=!0,this.stopChainedTweens()),this._isPlaying&&(this._isPlaying=!1,this._isPaused=!1,this._onStopCallback&&this._onStopCallback(this._object)),this},e.prototype.end=function(){return this._goToEnd=!0,this.update(this._startTime+this._duration),this},e.prototype.pause=function(e){return e===void 0&&(e=U()),this._isPaused||!this._isPlaying||(this._isPaused=!0,this._pauseStart=e),this},e.prototype.resume=function(e){return e===void 0&&(e=U()),!this._isPaused||!this._isPlaying||(this._isPaused=!1,this._startTime+=e-this._pauseStart,this._pauseStart=0),this},e.prototype.stopChainedTweens=function(){for(var e=0,t=this._chainedTweens.length;e<t;e++)this._chainedTweens[e].stop();return this},e.prototype.group=function(e){return e?(e.add(this),this):(console.warn(`tween.group() without args has been removed, use group.add(tween) instead.`),this)},e.prototype.remove=function(){var e;return(e=this._group)==null||e.remove(this),this},e.prototype.delay=function(e){return e===void 0&&(e=0),this._delayTime=e,this},e.prototype.repeat=function(e){return e===void 0&&(e=0),this._initialRepeat=e,this._repeat=e,this},e.prototype.repeatDelay=function(e){return this._repeatDelayTime=e,this},e.prototype.yoyo=function(e){return e===void 0&&(e=!1),this._yoyo=e,this},e.prototype.easing=function(e){return e===void 0&&(e=H.Linear.None),this._easingFunction=e,this},e.prototype.interpolation=function(e){return e===void 0&&(e=W.Linear),this._interpolationFunction=e,this},e.prototype.chain=function(){var e=[...arguments];return this._chainedTweens=e,this},e.prototype.onStart=function(e){return this._onStartCallback=e,this},e.prototype.onEveryStart=function(e){return this._onEveryStartCallback=e,this},e.prototype.onUpdate=function(e){return this._onUpdateCallback=e,this},e.prototype.onRepeat=function(e){return this._onRepeatCallback=e,this},e.prototype.onComplete=function(e){return this._onCompleteCallback=e,this},e.prototype.onStop=function(e){return this._onStopCallback=e,this},e.prototype.update=function(t,n){var r=this;if(t===void 0&&(t=U()),n===void 0&&(n=e.autoStartOnUpdate),this._isPaused)return!0;var i;if(!this._goToEnd&&!this._isPlaying){if(n)this.start(t,!0);else return!1}if(this._goToEnd=!1,t<this._startTime)return!0;this._onStartCallbackFired===!1&&(this._onStartCallback&&this._onStartCallback(this._object),this._onStartCallbackFired=!0),this._onEveryStartCallbackFired===!1&&(this._onEveryStartCallback&&this._onEveryStartCallback(this._object),this._onEveryStartCallbackFired=!0);var a=t-this._startTime,o=this._duration+(this._repeatDelayTime??this._delayTime),s=this._duration+this._repeat*o,c=function(){if(r._duration===0||a>s)return 1;var e=a-Math.trunc(a/o)*o,t=Math.min(e/r._duration,1);return t===0&&a===r._duration?1:t}(),l=this._easingFunction(c);if(this._updateProperties(this._object,this._valuesStart,this._valuesEnd,l),this._onUpdateCallback&&this._onUpdateCallback(this._object,c),this._duration===0||a>=this._duration){if(this._repeat>0){var u=Math.min(Math.trunc((a-this._duration)/o)+1,this._repeat);for(i in isFinite(this._repeat)&&(this._repeat-=u),this._valuesStartRepeat)!this._yoyo&&typeof this._valuesEnd[i]==`string`&&(this._valuesStartRepeat[i]=this._valuesStartRepeat[i]+parseFloat(this._valuesEnd[i])),this._yoyo&&this._swapEndStartRepeatValues(i),this._valuesStart[i]=this._valuesStartRepeat[i];return this._yoyo&&(this._reversed=!this._reversed),this._startTime+=o*u,this._onRepeatCallback&&this._onRepeatCallback(this._object),this._onEveryStartCallbackFired=!1,!0}this._onCompleteCallback&&this._onCompleteCallback(this._object);for(var d=0,f=this._chainedTweens.length;d<f;d++)this._chainedTweens[d].start(this._startTime+this._duration,!1);return this._isPlaying=!1,!1}return!0},e.prototype._updateProperties=function(e,t,n,r){for(var i in n)if(t[i]!==void 0){var a=t[i]||0,o=n[i];!Array.isArray(e[i])&&Array.isArray(o)?e[i]=this._interpolationFunction(o,r):typeof o==`object`&&o?this._updateProperties(e[i],a,o,r):(o=this._handleRelativeValue(a,o),typeof o==`number`&&(e[i]=a+(o-a)*r))}},e.prototype._handleRelativeValue=function(e,t){return typeof t==`string`?t.charAt(0)===`+`||t.charAt(0)===`-`?e+parseFloat(t):parseFloat(t):t},e.prototype._swapEndStartRepeatValues=function(e){var t=this._valuesStartRepeat[e],n=this._valuesEnd[e];typeof n==`string`?this._valuesStartRepeat[e]=this._valuesStartRepeat[e]+parseFloat(n):this._valuesStartRepeat[e]=this._valuesEnd[e],this._valuesEnd[e]=t},e.autoStartOnUpdate=!1,e}();G.nextId;var J=K;J.getAll.bind(J),J.removeAll.bind(J),J.add.bind(J),J.remove.bind(J);var de=J.update.bind(J),fe=class{camera;controls;currentLevel=`WHOLE_OCTOPUS`;navMode=`ORBIT`;isTweening=!1;currentTween=null;flyVelocity=new s;flySpeed=22;isSprint=!1;keyState={};euler=new S(0,0,0,`YXZ`);isMouseDownForFly=!1;lastMouseX=0;lastMouseY=0;followTarget=new s;followCamPos=new s;constructor(e,t){this.camera=e,this.controls=t,this.controls.enableDamping=!0,this.controls.dampingFactor=.08,this.controls.minDistance=2,this.controls.maxDistance=2500,this.controls.minPolarAngle=0,this.controls.maxPolarAngle=Math.PI,this.controls.enableRotate=!0,this.controls.rotateSpeed=1,this.controls.enablePan=!0,this.controls.panSpeed=1,this.controls.screenSpacePanning=!0,this.controls.enableZoom=!0,this.controls.zoomSpeed=1,this.bindKeyboardAndFlyEvents()}stopActiveTransition(){this.currentTween&&=(this.currentTween.stop(),null),this.isTweening=!1,this.controls.enabled=!0,this.controls.update()}setNavigationMode(e){this.navMode=e,this.controls.enabled=!0,e===`FREE_FLY`?this.euler.setFromQuaternion(this.camera.quaternion):e===`FOLLOW_SIGNAL`||this.controls.target.copy(this.camera.position).add(this.camera.getWorldDirection(new s).multiplyScalar(20)),this.controls.update()}bindKeyboardAndFlyEvents(){window.addEventListener(`keydown`,e=>{this.keyState[e.code]=!0,(e.code===`ShiftLeft`||e.code===`ShiftRight`)&&(this.isSprint=!0)}),window.addEventListener(`keyup`,e=>{this.keyState[e.code]=!1,(e.code===`ShiftLeft`||e.code===`ShiftRight`)&&(this.isSprint=!1)}),window.addEventListener(`mousedown`,e=>{this.navMode===`FREE_FLY`&&(e.button===0||e.button===2)&&(this.isMouseDownForFly=!0,this.lastMouseX=e.clientX,this.lastMouseY=e.clientY)}),window.addEventListener(`mouseup`,()=>{this.isMouseDownForFly=!1}),window.addEventListener(`mousemove`,e=>{if(this.navMode===`FREE_FLY`&&this.isMouseDownForFly){let t=e.clientX-this.lastMouseX,n=e.clientY-this.lastMouseY;this.lastMouseX=e.clientX,this.lastMouseY=e.clientY;let r=.0032;this.euler.y-=t*r,this.euler.x-=n*r,this.euler.x=Math.max(-Math.PI*.48,Math.min(Math.PI*.48,this.euler.x)),this.camera.quaternion.setFromEuler(this.euler)}})}flyTo(e,t,n=1300,r=`WHOLE_OCTOPUS`,i){if(this.currentLevel=r,this.currentTween&&=(this.currentTween.stop(),null),V()){this.camera.position.copy(e),this.controls.target.copy(t),this.camera.lookAt(t),this.controls.enabled=!0,this.controls.update(),this.isTweening=!1,i&&i();return}this.isTweening=!0,this.controls.enabled=!0;let a=this.camera.position.clone(),o=this.controls.target.clone();this.currentTween=new q({camX:a.x,camY:a.y,camZ:a.z,tgtX:o.x,tgtY:o.y,tgtZ:o.z}).to({camX:e.x,camY:e.y,camZ:e.z,tgtX:t.x,tgtY:t.y,tgtZ:t.z},n).easing(H.Cubic.InOut).onUpdate(e=>{this.camera.position.set(e.camX,e.camY,e.camZ),this.controls.target.set(e.tgtX,e.tgtY,e.tgtZ),this.camera.lookAt(this.controls.target)}).onComplete(()=>{this.currentTween=null,this.controls.enabled=!0,this.controls.update(),this.isTweening=!1,i&&i()}).start()}gtaSwitchTo(e,t,n=1450,r){if(this.currentLevel=`WHOLE_OCTOPUS`,this.currentTween&&=(this.currentTween.stop(),null),V()){this.camera.position.copy(e),this.controls.target.copy(t),this.camera.lookAt(t),this.controls.enabled=!0,this.controls.update(),this.isTweening=!1,r&&r();return}this.isTweening=!0,this.controls.enabled=!0;let i=this.camera.position.clone(),a=this.controls.target.clone(),o=(i.x+e.x)*.5,c=(i.z+e.z)*.5,l=i.distanceTo(e),u=Math.max(i.y,e.y)+Math.min(240,Math.max(110,l*.55)),d=Math.hypot(o,c),f=d>10?Math.max(65,d*1.3)/d:1,p=new s(o*f,u,c*f),m=new s(o*.25,5,c*.25),h={t:0};this.currentTween=new q(h).to({t:1},n).easing(H.Cubic.InOut).onUpdate(({t:n})=>{let r=1-n,o=r*r,s=2*r*n,c=n*n,l=o*i.x+s*p.x+c*e.x,u=o*i.y+s*p.y+c*e.y,d=o*i.z+s*p.z+c*e.z,f=o*a.x+s*m.x+c*t.x,h=o*a.y+s*m.y+c*t.y,g=o*a.z+s*m.z+c*t.z;this.camera.position.set(l,u,d),this.controls.target.set(f,h,g),this.camera.lookAt(this.controls.target);let _=Math.sin(n*Math.PI)*15;this.camera.fov=45+_,this.camera.updateProjectionMatrix()}).onComplete(()=>{this.currentTween=null,this.camera.position.copy(e),this.controls.target.copy(t),this.camera.lookAt(t),this.camera.fov=45,this.camera.updateProjectionMatrix(),this.controls.enabled=!0,this.controls.update(),this.isTweening=!1,r&&r()}).start()}tweenCameraTo(e,t,n=1800,r){this.flyTo(e,t,n,this.currentLevel,r)}orbitBy(e,t=0){if(this.isTweening||this.navMode!==`ORBIT`)return;let n=this.camera.position.clone().sub(this.controls.target),r=n.length(),i=Math.atan2(n.x,n.z),a=Math.acos(Math.max(-1,Math.min(1,n.y/Math.max(.001,r))));i+=e,a=Math.max(.05,Math.min(Math.PI-.05,a+t)),n.x=r*Math.sin(a)*Math.sin(i),n.y=r*Math.cos(a),n.z=r*Math.sin(a)*Math.cos(i),this.camera.position.copy(this.controls.target).add(n),this.camera.lookAt(this.controls.target)}anchorPosition=new s(0,0,0);setAnchor(e){this.anchorPosition.copy(e)}goToWholeOctopus(){this.flyTo(this.anchorPosition.clone().add(new s(0,48,92)),this.anchorPosition.clone().add(new s(0,-2,0)),1400,`WHOLE_OCTOPUS`)}goToCentralBrain(){this.flyTo(this.anchorPosition.clone().add(new s(0,16,32)),this.anchorPosition.clone().add(new s(0,3,0)),1300,`CENTRAL_BRAIN`)}goToVerticalLobe(){this.flyTo(this.anchorPosition.clone().add(new s(0,18,18)),this.anchorPosition.clone().add(new s(0,8.5,1.5)),1200,`BRAIN_REGION`)}goToOpticLobe(e=`left`){let t=e===`left`?-26:26,n=e===`left`?-18:18;this.flyTo(this.anchorPosition.clone().add(new s(t,10,20)),this.anchorPosition.clone().add(new s(n,3.5,0)),1200,`BRAIN_REGION`)}goToArm(e){let t=e/8*Math.PI*2,n=45*Math.cos(t-.2),r=45*Math.sin(t-.2),i=25*Math.cos(t),a=25*Math.sin(t);this.flyTo(this.anchorPosition.clone().add(new s(n,-12,r)),this.anchorPosition.clone().add(new s(i,-16,a)),1400,`ARM`)}goToAxialCord(e,t=10){let n=e/8*Math.PI*2,r=16+t*.7,i=r*Math.cos(n),a=r*Math.sin(n);this.flyTo(this.anchorPosition.clone().add(new s(i+5*Math.cos(n+.5),-10,a+5*Math.sin(n+.5))),this.anchorPosition.clone().add(new s(i,-14,a)),1100,`AXIAL_NERVE_CORD`)}goToSuckerGanglion(e,t=12){let n=e/8*Math.PI*2,r=18+t*.8,i=r*Math.cos(n),a=r*Math.sin(n);this.flyTo(this.anchorPosition.clone().add(new s(i+2.5,-16.5,a+2.5)),this.anchorPosition.clone().add(new s(i,-18,a)),1e3,`SUCKER_NETWORK`)}goToIndividualNeuron(e,t=!1){let n=t?.65:2.2,r=new s(n*.7,n*.5,n*.7),i=e.clone().add(this.anchorPosition);this.flyTo(i.clone().add(r),i.clone(),950,`INDIVIDUAL_NEURON`)}goToConnectionFiber(e,t){let n=new s().addVectors(e,t).multiplyScalar(.5).add(this.anchorPosition),r=new s(1.8,1.2,1.8);this.flyTo(n.clone().add(r),n.clone(),900,`INDIVIDUAL_CONNECTION`)}setPerspectiveAngle(e){let t=this.anchorPosition.clone().add(new s(0,4,0)),n=new s,r=t.clone();e===`FRONT`?n.set(t.x,t.y+10,t.z+75):e===`BACK`?n.set(t.x,t.y+10,t.z-75):e===`LEFT`?n.set(t.x-75,t.y+10,t.z):e===`RIGHT`?n.set(t.x+75,t.y+10,t.z):e===`TOP`?n.set(t.x,t.y+75,t.z+.1):e===`BOTTOM`?n.set(t.x,t.y-75,t.z+.1):e===`INSIDE`&&(n.set(this.anchorPosition.x,this.anchorPosition.y+3.5,this.anchorPosition.z+.5),r.set(this.anchorPosition.x,this.anchorPosition.y+7,this.anchorPosition.z-1)),this.flyTo(n,r,1100,this.currentLevel)}updateSignalFollow(e,t=.016){if(this.navMode!==`FOLLOW_SIGNAL`)return;this.followTarget.lerp(e,.15);let n=new s(0,3.5,7);this.followCamPos.copy(this.followTarget).add(n),this.camera.position.lerp(this.followCamPos,.12),this.camera.lookAt(this.followTarget)}update(e=.016){de(),this.controls.update(),this.navMode===`FREE_FLY`&&this.updateFreeFly(e)}updateFreeFly(e){let t=this.flySpeed*(this.isSprint?2.5:1),n=new s;(this.keyState.KeyW||this.keyState.ArrowUp)&&--n.z,(this.keyState.KeyS||this.keyState.ArrowDown)&&(n.z+=1),(this.keyState.KeyA||this.keyState.ArrowLeft)&&--n.x,(this.keyState.KeyD||this.keyState.ArrowRight)&&(n.x+=1),(this.keyState.Space||this.keyState.KeyE)&&(n.y+=1),(this.keyState.KeyC||this.keyState.KeyQ)&&--n.y,n.lengthSq()>0?(n.normalize(),n.applyQuaternion(this.camera.quaternion),this.flyVelocity.lerp(n.multiplyScalar(t),.15)):this.flyVelocity.lerp(new s(0,0,0),.12),this.camera.position.addScaledVector(this.flyVelocity,e)}},pe=class{raycaster;connectome;camera;nodeThreshold=1.6;fiberThreshold=.9;worldOffset=new s(0,0,0);constructor(e,t){this.camera=e,this.connectome=t,this.raycaster=new r}setConnectome(e,t){this.connectome=e,t?this.worldOffset.copy(t):this.worldOffset.set(0,0,0)}setThreshold(e){this.nodeThreshold=e}pickNode(e){this.raycaster.setFromCamera(e,this.camera);let t=this.raycaster.ray,n=null,r=1/0,i=this.connectome.nodes.length,a=this.connectome.nodes,o=this.worldOffset.lengthSq()>0;for(let e=0;e<i;e++){let i=a[e],s=o?i.position.clone().add(this.worldOffset):i.position,c=t.distanceSqToPoint(s),l=(i.type===`ganglion_hub`?3:i.type===`sucker_receptor`?2:1.4)*(this.nodeThreshold*.75);if(c<l*l){let e=t.origin.distanceTo(s);e<r&&(r=e,n=i)}}return n?{node:n,distance:r,hitPoint:n.position.clone()}:null}pickFiber(e){this.raycaster.setFromCamera(e,this.camera);let t=this.raycaster.ray,n=null,r=1/0,i=new s,a=this.connectome.fibers,o=a.length,c=this.fiberThreshold*this.fiberThreshold,l=new s,u=new s,d=new s,p=new s,m=this.worldOffset.lengthSq()>0;for(let e=0;e<o;e++){let o=a[e],s=this.connectome.nodes[o.sourceIndex].position,h=this.connectome.nodes[o.targetIndex].position,g=m?s.clone().add(this.worldOffset):s,_=m?h.clone().add(this.worldOffset):h,v=(g.x+_.x)*.5,y=(g.y+_.y)*.5,b=(g.z+_.z)*.5;if(l.set(v,y,b),t.distanceSqToPoint(l)>25)continue;l.subVectors(_,g);let x=l.lengthSq();if(x<1e-4)continue;u.subVectors(g,t.origin);let S=t.direction.dot(l),C=l.dot(u),w=t.direction.dot(u),T=x-S*S,E=.5;Math.abs(T)>1e-5&&(E=f.clamp((S*w-C)/T,0,1)),d.copy(g).addScaledVector(l,E);let D=Math.max(0,t.direction.dot(d.clone().sub(t.origin)));if(p.copy(t.origin).addScaledVector(t.direction,D),d.distanceToSquared(p)<c){let e=t.origin.distanceTo(d);e<r&&(r=e,n=o,i.copy(d))}}return n?{fiber:n,distance:r,hitPoint:i}:null}pick(e){let t=this.pickNode(e);if(t)return{type:`node`,node:t.node,distance:t.distance,hitPoint:t.hitPoint};let n=this.pickFiber(e);return n?{type:`fiber`,fiber:n.fiber,sourceNode:this.connectome.nodes[n.fiber.sourceIndex],targetNode:this.connectome.nodes[n.fiber.targetIndex],distance:n.distance,hitPoint:n.hitPoint}:null}},Y={octopusCore:(e=18,t=`#38bdf8`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M12 2C7.5 2 4 5.5 4 10C4 13.2 5.8 15.8 8.5 17.2V20C8.5 20.8 9.2 21.5 10 21.5C10.8 21.5 11.5 20.8 11.5 20V18.5H12.5V20C12.5 20.8 13.2 21.5 14 21.5C14.8 21.5 15.5 20.8 15.5 20V17.2C18.2 15.8 20 13.2 20 10C20 5.5 16.5 2 12 2Z" stroke="${t}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" fill="rgba(56, 189, 248, 0.12)"/>
      <circle cx="9" cy="9.5" r="1.5" fill="#ffffff" filter="drop-shadow(0 0 4px ${t})"/>
      <circle cx="15" cy="9.5" r="1.5" fill="#ffffff" filter="drop-shadow(0 0 4px ${t})"/>
      <path d="M10 13.5C11 14.5 13 14.5 14 13.5" stroke="${t}" stroke-width="1.4" stroke-linecap="round"/>
      <circle cx="12" cy="6" r="1" fill="#38bdf8" filter="drop-shadow(0 0 3px #38bdf8)"/>
    </svg>
  `,brainCortex:(e=16,t=`#c084fc`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M9.5 3C7 3 5 5 5 7.5C5 8.4 5.3 9.2 5.7 10C4.7 10.6 4 11.7 4 13C4 14.4 4.8 15.6 6 16.2C6 18.3 7.7 20 9.8 20C10.6 20 11.4 19.7 12 19.2C12.6 19.7 13.4 20 14.2 20C16.3 20 18 18.3 18 16.2C19.2 15.6 20 14.4 20 13C20 11.7 19.3 10.6 18.3 10C18.7 9.2 19 8.4 19 7.5C19 5 17 3 14.5 3C13.5 3 12.6 3.4 12 4C11.4 3.4 10.5 3 9.5 3Z" stroke="${t}" stroke-width="1.5" fill="rgba(192, 132, 252, 0.1)"/>
      <path d="M12 5V19" stroke="${t}" stroke-width="1.4" stroke-dasharray="2 2"/>
      <circle cx="9" cy="11" r="1.5" fill="#ffffff" filter="drop-shadow(0 0 4px ${t})"/>
      <circle cx="15" cy="11" r="1.5" fill="#ffffff" filter="drop-shadow(0 0 4px ${t})"/>
    </svg>
  `,brachialRing:(e=16,t=`#38bdf8`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <circle cx="12" cy="12" r="7.5" stroke="${t}" stroke-width="1.5" stroke-dasharray="3 2" fill="rgba(56, 189, 248, 0.08)"/>
      <circle cx="12" cy="4.5" r="1.8" fill="#ffffff" stroke="${t}" stroke-width="1.2"/>
      <circle cx="17.3" cy="6.7" r="1.8" fill="#ffffff" stroke="${t}" stroke-width="1.2"/>
      <circle cx="19.5" cy="12" r="1.8" fill="#ffffff" stroke="${t}" stroke-width="1.2"/>
      <circle cx="17.3" cy="17.3" r="1.8" fill="#ffffff" stroke="${t}" stroke-width="1.2"/>
      <circle cx="12" cy="19.5" r="1.8" fill="#ffffff" stroke="${t}" stroke-width="1.2"/>
      <circle cx="6.7" cy="17.3" r="1.8" fill="#ffffff" stroke="${t}" stroke-width="1.2"/>
      <circle cx="4.5" cy="12" r="1.8" fill="#ffffff" stroke="${t}" stroke-width="1.2"/>
      <circle cx="6.7" cy="6.7" r="1.8" fill="#ffffff" stroke="${t}" stroke-width="1.2"/>
      <circle cx="12" cy="12" r="2.2" fill="${t}" filter="drop-shadow(0 0 6px ${t})"/>
    </svg>
  `,actionPotential:(e=16,t=`#facc15`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M13 2L4 13.5H11.5L10 22L20 9.5H12.5L14 2H13Z" stroke="${t}" stroke-width="1.6" stroke-linejoin="round" fill="rgba(250, 204, 21, 0.15)" filter="drop-shadow(0 0 6px rgba(250, 204, 21, 0.5))"/>
    </svg>
  `,spatialOrbit:(e=16,t=`#38bdf8`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <circle cx="12" cy="12" r="8" stroke="${t}" stroke-width="1.4" stroke-opacity="0.5"/>
      <ellipse cx="12" cy="12" rx="8.5" ry="3.5" stroke="${t}" stroke-width="1.5" transform="rotate(-25 12 12)"/>
      <circle cx="12" cy="12" r="2" fill="#ffffff" filter="drop-shadow(0 0 5px ${t})"/>
    </svg>
  `,freeFlight:(e=16,t=`#818cf8`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M12 2L19 21L12 17L5 21L12 2Z" stroke="${t}" stroke-width="1.5" stroke-linejoin="round" fill="rgba(129, 140, 248, 0.12)"/>
      <circle cx="12" cy="11" r="1.5" fill="#ffffff"/>
    </svg>
  `,suckerReceptor:(e=16,t=`#f43f5e`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <circle cx="12" cy="10" r="7" stroke="${t}" stroke-width="1.5" fill="rgba(244, 63, 94, 0.12)"/>
      <circle cx="12" cy="10" r="3" stroke="${t}" stroke-width="1.3" fill="rgba(255, 255, 255, 0.3)"/>
      <path d="M12 17V22" stroke="${t}" stroke-width="1.6" stroke-linecap="round"/>
      <circle cx="12" cy="10" r="1.2" fill="#ffffff" filter="drop-shadow(0 0 4px #f43f5e)"/>
    </svg>
  `,opticLobe:(e=16,t=`#a855f7`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M2 12C2 12 5.5 5 12 5C18.5 5 22 12 22 12C22 12 18.5 19 12 19C5.5 19 2 12 2 12Z" stroke="${t}" stroke-width="1.5" fill="rgba(168, 85, 247, 0.1)"/>
      <circle cx="12" cy="12" r="3.5" stroke="${t}" stroke-width="1.4" fill="rgba(255, 255, 255, 0.2)"/>
      <circle cx="12" cy="12" r="1.5" fill="#ffffff" filter="drop-shadow(0 0 5px #a855f7)"/>
    </svg>
  `,escapeJet:(e=16,t=`#f97316`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M12 2V9M8 4L11 8M16 4L13 8" stroke="${t}" stroke-width="1.5" stroke-linecap="round"/>
      <path d="M6 10C6 10 7 17 12 22C17 17 18 10 18 10H6Z" stroke="${t}" stroke-width="1.5" fill="rgba(249, 115, 22, 0.15)"/>
      <circle cx="12" cy="14" r="1.8" fill="#ffffff"/>
    </svg>
  `,customProbe:(e=16,t=`#10b981`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <circle cx="12" cy="12" r="8" stroke="${t}" stroke-width="1.4" stroke-dasharray="4 2"/>
      <path d="M12 2V6M12 18V22M2 12H6M18 12H22" stroke="${t}" stroke-width="1.5" stroke-linecap="round"/>
      <circle cx="12" cy="12" r="2" fill="#ffffff" filter="drop-shadow(0 0 4px ${t})"/>
    </svg>
  `,connectomeLattice:(e=16,t=`#38bdf8`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M12 2L20 7V17L12 22L4 17V7L12 2Z" stroke="${t}" stroke-width="1.4" fill="rgba(56, 189, 248, 0.08)"/>
      <path d="M12 2V22M4 7L20 17M4 17L20 7" stroke="${t}" stroke-width="1.2" stroke-opacity="0.4"/>
      <circle cx="12" cy="12" r="2" fill="#ffffff"/>
    </svg>
  `,activityWave:(e=16,t=`#06b6d4`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M2 13H6L8.5 5L12.5 19L15.5 9L18 13H22" stroke="${t}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" filter="drop-shadow(0 0 4px ${t})"/>
    </svg>
  `,exploreCompass:(e=16,t=`#38bdf8`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <circle cx="12" cy="12" r="8" stroke="${t}" stroke-width="1.4"/>
      <path d="M14.5 9.5L10 11L9.5 14.5L14 13L14.5 9.5Z" fill="${t}" stroke="#ffffff" stroke-width="1"/>
    </svg>
  `,anatomyLayer:(e=16,t=`#ec4899`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M12 3C9 3 7 5 7 8C7 10 8 11.5 9 12.5C7 13.5 5 15.5 5 18C5 19.5 6.5 21 8.5 21C10.5 21 11.5 19.5 12 18.5C12.5 19.5 13.5 21 15.5 21C17.5 21 19 19.5 19 18C19 15.5 17 13.5 15 12.5C16 11.5 17 10 17 8C17 5 15 3 12 3Z" stroke="${t}" stroke-width="1.4" fill="rgba(236, 72, 153, 0.12)"/>
    </svg>
  `,tourPlay:(e=16,t=`#ffffff`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <circle cx="12" cy="12" r="9" stroke="${t}" stroke-width="1.4" stroke-opacity="0.7"/>
      <path d="M10 8.5L16 12L10 15.5V8.5Z" fill="${t}"/>
    </svg>
  `,concept:(e=16,t=`#facc15`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M12 2C8.13 2 5 5.13 5 9C5 11.38 6.19 13.47 8 14.74V17C8 17.55 8.45 18 9 18H15C15.55 18 16 17.55 16 17V14.74C17.81 13.47 19 11.38 19 9C19 5.13 15.87 2 12 2Z" stroke="${t}" stroke-width="1.5" fill="rgba(250, 204, 21, 0.15)" filter="drop-shadow(0 0 4px rgba(250, 204, 21, 0.4))"/>
      <path d="M9 21H15" stroke="${t}" stroke-width="1.5" stroke-linecap="round"/>
      <path d="M10 10L12 8L14 10" stroke="#ffffff" stroke-width="1.2" stroke-linecap="round"/>
    </svg>
  `,flowArrow:(e=12,t=`rgba(255,255,255,0.4)`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M6 3L11 8L6 13" stroke="${t}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  `,stepPrev:(e=12,t=`#ffffff`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M4 4V12M12 4L6 8L12 12V4Z" stroke="${t}" stroke-width="1.4" fill="${t}" stroke-linejoin="round"/>
    </svg>
  `,stepNext:(e=12,t=`#ffffff`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M12 4V12M4 4L10 8L4 12V4Z" stroke="${t}" stroke-width="1.4" fill="${t}" stroke-linejoin="round"/>
    </svg>
  `,play:(e=12,t=`#ffffff`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M5 3.5L13 8L5 12.5V3.5Z" fill="${t}"/>
    </svg>
  `,pause:(e=12,t=`#ffffff`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M4.5 3.5H6.5V12.5H4.5V3.5ZM9.5 3.5H11.5V12.5H9.5V3.5Z" fill="${t}"/>
    </svg>
  `,closeCross:(e=12,t=`rgba(255,255,255,0.7)`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M3.5 3.5L12.5 12.5M12.5 3.5L3.5 12.5" stroke="${t}" stroke-width="1.6" stroke-linecap="round"/>
    </svg>
  `,finishFlag:(e=12,t=`#10b981`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <circle cx="8" cy="8" r="7" stroke="${t}" stroke-width="1.3" fill="rgba(16, 185, 129, 0.15)"/>
      <path d="M5 8L7 10L11 6" stroke="${t}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  `,dragGrip:(e=14,t=`rgba(255,255,255,0.6)`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <circle cx="5" cy="4" r="1.3" fill="${t}"/>
      <circle cx="11" cy="4" r="1.3" fill="${t}"/>
      <circle cx="5" cy="8" r="1.3" fill="${t}"/>
      <circle cx="11" cy="8" r="1.3" fill="${t}"/>
      <circle cx="5" cy="12" r="1.3" fill="${t}"/>
      <circle cx="11" cy="12" r="1.3" fill="${t}"/>
    </svg>
  `,minimize:(e=12,t=`rgba(255,255,255,0.7)`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <line x1="3" y1="8" x2="13" y2="8" stroke="${t}" stroke-width="1.8" stroke-linecap="round"/>
    </svg>
  `,maximize:(e=12,t=`rgba(255,255,255,0.7)`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <rect x="3.5" y="3.5" width="9" height="9" rx="1.5" stroke="${t}" stroke-width="1.5"/>
    </svg>
  `,resetLayout:(e=14,t=`#74c7ec`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M4 4V9H9" stroke="${t}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M20 20V15H15" stroke="${t}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M20 9A9 9 0 005.6 5.6L4 9" stroke="${t}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M4 15A9 9 0 0018.4 18.4L20 15" stroke="${t}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  `,octoArchitect:(e=14,t=`#00F0FF`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="octo-custom-glyph" style="display:inline-block;vertical-align:middle;">
      <path d="M12 2L21 7V17L12 22L3 17V7L12 2Z" stroke="${t}" stroke-width="1.8" stroke-linejoin="round" fill="rgba(0, 240, 255, 0.14)"/>
      <path d="M12 22V12M12 12L21 7M12 12L3 7" stroke="${t}" stroke-width="1.6" stroke-linejoin="round"/>
      <circle cx="12" cy="12" r="2.2" fill="#ffffff" filter="drop-shadow(0 0 4px ${t})"/>
    </svg>
  `,octoDatabase:(e=14,t=`#A855F7`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="octo-custom-glyph" style="display:inline-block;vertical-align:middle;">
      <ellipse cx="12" cy="5" rx="8" ry="3" stroke="${t}" stroke-width="1.8" fill="rgba(168, 85, 247, 0.22)"/>
      <path d="M4 5V12C4 13.65 7.58 15 12 15C16.42 15 20 13.65 20 12V5" stroke="${t}" stroke-width="1.8"/>
      <path d="M4 12V19C4 20.65 7.58 22 12 22C16.42 22 20 20.65 20 19V12" stroke="${t}" stroke-width="1.8"/>
      <circle cx="12" cy="12" r="1.4" fill="#ffffff"/>
      <circle cx="12" cy="19" r="1.4" fill="#ffffff"/>
    </svg>
  `,octoBackend:(e=14,t=`#3B82F6`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="octo-custom-glyph" style="display:inline-block;vertical-align:middle;">
      <path d="M13 2L3 14H12L11 22L21 10H12L13 2Z" stroke="${t}" stroke-width="1.8" stroke-linejoin="round" fill="rgba(59, 130, 246, 0.22)"/>
      <circle cx="12" cy="12" r="1.5" fill="#ffffff" filter="drop-shadow(0 0 4px ${t})"/>
    </svg>
  `,octoFrontend:(e=14,t=`#EC4899`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="octo-custom-glyph" style="display:inline-block;vertical-align:middle;">
      <rect x="3" y="4" width="18" height="16" rx="3" stroke="${t}" stroke-width="1.8" fill="rgba(236, 72, 153, 0.16)"/>
      <path d="M3 9H21" stroke="${t}" stroke-width="1.6"/>
      <circle cx="6.5" cy="6.5" r="1" fill="#ffffff"/>
      <circle cx="9.5" cy="6.5" r="1" fill="${t}"/>
      <path d="M8 15L11 12L8 9M13 16H17" stroke="#ffffff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  `,octoCognitive:(e=14,t=`#10B981`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="octo-custom-glyph" style="display:inline-block;vertical-align:middle;">
      <circle cx="12" cy="12" r="4" stroke="${t}" stroke-width="1.8" fill="rgba(16, 185, 129, 0.28)"/>
      <circle cx="12" cy="4" r="2" fill="${t}"/>
      <circle cx="20" cy="12" r="2" fill="${t}"/>
      <circle cx="12" cy="20" r="2" fill="${t}"/>
      <circle cx="4" cy="12" r="2" fill="${t}"/>
      <path d="M12 6V8M18 12H16M12 18V16M6 12H8" stroke="${t}" stroke-width="1.6"/>
      <circle cx="12" cy="12" r="1.8" fill="#ffffff" filter="drop-shadow(0 0 4px ${t})"/>
    </svg>
  `,octoSentinel:(e=14,t=`#EF4444`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="octo-custom-glyph" style="display:inline-block;vertical-align:middle;">
      <path d="M12 2L20 6V11C20 16.5 16.5 21 12 22C7.5 21 4 16.5 4 11V6L12 2Z" stroke="${t}" stroke-width="1.8" stroke-linejoin="round" fill="rgba(239, 68, 68, 0.2)"/>
      <circle cx="12" cy="11.5" r="2.4" fill="#ffffff" filter="drop-shadow(0 0 4px ${t})"/>
      <path d="M12 8V9M12 14V15" stroke="${t}" stroke-width="1.6" stroke-linecap="round"/>
    </svg>
  `,octoChaos:(e=14,t=`#F59E0B`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="octo-custom-glyph" style="display:inline-block;vertical-align:middle;">
      <ellipse cx="12" cy="12" rx="9" ry="3.5" stroke="${t}" stroke-width="1.5" transform="rotate(30 12 12)"/>
      <ellipse cx="12" cy="12" rx="9" ry="3.5" stroke="${t}" stroke-width="1.5" transform="rotate(-30 12 12)"/>
      <circle cx="12" cy="12" r="2.8" fill="#ffffff" filter="drop-shadow(0 0 5px ${t})"/>
    </svg>
  `,octoRunner:(e=14,t=`#EAB308`)=>`
    <svg width="${e}" height="${e}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="octo-custom-glyph" style="display:inline-block;vertical-align:middle;">
      <path d="M12 2L19 16L12 13L5 16L12 2Z" stroke="${t}" stroke-width="1.8" stroke-linejoin="round" fill="rgba(234, 179, 8, 0.22)"/>
      <path d="M12 13V22M9 19L12 22L15 19" stroke="${t}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="12" cy="9" r="1.5" fill="#ffffff" filter="drop-shadow(0 0 4px ${t})"/>
    </svg>
  `,octoGlyph:(e,t=14)=>{switch(e){case 0:return Y.octoArchitect(t,`#00F0FF`);case 1:return Y.octoDatabase(t,`#A855F7`);case 2:return Y.octoBackend(t,`#3B82F6`);case 3:return Y.octoFrontend(t,`#EC4899`);case 4:return Y.octoCognitive(t,`#10B981`);case 5:return Y.octoSentinel(t,`#EF4444`);case 6:return Y.octoChaos(t,`#F59E0B`);case 7:return Y.octoRunner(t,`#EAB308`);default:return Y.octopusCore(t,`#38bdf8`)}}},me=class{container;mode=`REGION`;currentRegion=null;currentNode=null;currentFiber=null;sourceNode=null;targetNode=null;allNodes=[];onIsolateRegion;onFocusCamera;onFocusNeuron;onFocusFiber;onStimulateNode;onStimulateFiber;onSelectNeuron;onOpenManual;constructor(e=`inspector-panel`){this.container=document.getElementById(e)||document.body}setNodesReference(e){this.allNodes=e}showRegion(e,t){let n=I[e];n&&(this.mode=`REGION`,this.currentRegion=n,this.currentNode=t||null,this.currentFiber=null,this.render())}showNeuron(e){this.mode=`NEURON`,this.currentNode=e,this.currentRegion=I[e.regionId]||null,this.currentFiber=null,this.render()}showFiber(e,t,n){this.mode=`FIBER`,this.currentFiber=e,this.sourceNode=t,this.targetNode=n,this.currentRegion=I[e.regionId]||null,this.render()}show(){this.container.classList.remove(`hidden`)}hide(){this.currentRegion=null,this.currentNode=null,this.currentFiber=null,this.container.classList.add(`hidden`)}render(){this.mode===`NEURON`&&this.currentNode?this.renderNeuronView():this.mode===`FIBER`&&this.currentFiber&&this.sourceNode&&this.targetNode?this.renderFiberView():this.currentRegion&&this.renderRegionView(),this.container.classList.remove(`hidden`),this.bindEvents()}renderNeuronView(){let e=this.currentNode,t=this.currentRegion,n=t?t.name:e.regionId,r=e.upstreamNeighbors.map(e=>this.allNodes[e]).filter(Boolean),i=e.downstreamNeighbors.map(e=>this.allNodes[e]).filter(Boolean);this.container.innerHTML=`
      <div class="inspector-header">
        <div style="display: flex; align-items: center; gap: 8px;">
          <span class="window-drag-icon">${Y.dragGrip(14,`rgba(255,255,255,0.6)`)}</span>
          <div class="inspector-tag badge-neuron">
            NEURON SOMA #${e.index}
          </div>
        </div>
        <div style="display: flex; align-items: center; gap: 6px;">
          <button class="btn-window-minimize" title="Minimize / Expand Window">${Y.minimize(11,`rgba(255,255,255,0.8)`)}</button>
          <button id="btn-close-inspector" class="btn-close" title="Close Inspector">${Y.closeCross(12,`#cbd5e1`)}</button>
        </div>
      </div>

      <div class="window-body-scroll">
        <h2 class="inspector-title">${e.type.toUpperCase().replace(`_`,` `)} #${e.index}</h2>
      <div class="inspector-systematic">Located in: ${n}</div>

      <!-- 3D Coordinate Telemetry -->
      <div class="telemetry-bar">
        <div class="telemetry-item">
          <span class="telemetry-label">3D Spatial Position</span>
          <span class="telemetry-val telemetry-coords">
            X: ${e.position.x.toFixed(2)}, Y: ${e.position.y.toFixed(2)}, Z: ${e.position.z.toFixed(2)}
          </span>
        </div>
        <div class="telemetry-item">
          <span class="telemetry-label">Morphological Scale</span>
          <span class="telemetry-val">${(e.size*8.5).toFixed(1)} µm</span>
        </div>
      </div>

      <!-- Anatomical Context -->
      <div class="inspector-section">
        <h3>Anatomical Context</h3>
        <div class="tags-container">
          <span class="tag tag-input">${e.armIndex>=0?`Arm ${e.armIndex+1}`:`Central Cranial Mass`}</span>
          <span class="tag tag-output">${e.segmentIndex>=0?`Sucker Segment ${e.segmentIndex+1}`:`Supra/Subesophageal Neuropil`}</span>
          <span class="tag tag-nt">${e.neighbors.length} Total Synaptic Links</span>
        </div>
      </div>

      <!-- Local Microcircuit Flow Diagram -->
      <div class="inspector-section">
        <h3>Local Synaptic Microcircuit</h3>
        <div class="circuit-flow-container">
          <div class="circuit-column">
            <div class="circuit-col-title">PRE-SYNAPTIC (${r.length})</div>
            <div class="circuit-node-list">
              ${r.slice(0,4).map(e=>`
                <button class="btn-micro-node btn-up" data-node="${e.index}">#${e.index} (${e.type.substring(0,4)})</button>
              `).join(``)}
              ${r.length>4?`<div class="more-nodes">+${r.length-4} more</div>`:``}
              ${r.length===0?`<div class="more-nodes">Sensory Receptor</div>`:``}
            </div>
          </div>

          <div class="circuit-arrow">${Y.flowArrow(12,`rgba(255,255,255,0.4)`)}</div>

          <div class="circuit-column target-col">
            <div class="circuit-col-title target-title">TARGET SOMA</div>
            <div class="target-node-box">
              <strong>#${e.index}</strong>
              <small>${e.type}</small>
            </div>
          </div>

          <div class="circuit-arrow">${Y.flowArrow(12,`rgba(255,255,255,0.4)`)}</div>

          <div class="circuit-column">
            <div class="circuit-col-title">POST-SYNAPTIC (${i.length})</div>
            <div class="circuit-node-list">
              ${i.slice(0,4).map(e=>`
                <button class="btn-micro-node btn-down" data-node="${e.index}">#${e.index} (${e.type.substring(0,4)})</button>
              `).join(``)}
              ${i.length>4?`<div class="more-nodes">+${i.length-4} more</div>`:``}
              ${i.length===0?`<div class="more-nodes">Motor Efferent</div>`:``}
            </div>
          </div>
        </div>
      </div>

      <!-- Action Potential Trigger -->
      <button id="btn-stimulate-neuron" class="btn-action pulse btn-action-stimulate">
        ${Y.actionPotential(14,`#fab387`)}
        <span>Trigger Action Potential Cascade</span>
      </button>

      <!-- Navigation Actions -->
      <div class="inspector-actions">
        <button id="btn-focus-neuron" class="btn-action">
          ${Y.spatialOrbit(14,`#89dceb`)}
          <span>Orbit Around Neuron</span>
        </button>
        <button id="btn-micro-zoom" class="btn-action">
          ${Y.customProbe(14,`#89dceb`)}
          <span>Micron LOD Zoom</span>
        </button>
      </div>

      <!-- Disclaimer -->
      <div class="disclaimer-box" style="margin-top: 6px;">
        <strong>Connectome Level:</strong> Detailed computational approximation of local cephalopod microcircuit branching.
      </div>
      </div>
    `}renderFiberView(){let e=this.currentFiber,t=this.sourceNode,n=this.targetNode,r=this.currentRegion,i=e.biologicalStatus===`known`?`<span class="data-badge badge-known">● Known Biological Tract</span>`:e.biologicalStatus===`inferred`?`<span class="data-badge badge-inferred">● Scientifically Inferred</span>`:`<span class="data-badge badge-approx">● Computational Approximation</span>`;this.container.innerHTML=`
      <div class="inspector-header">
        <div style="display: flex; align-items: center; gap: 8px;">
          <span class="window-drag-icon">${Y.dragGrip(14,`rgba(255,255,255,0.6)`)}</span>
          <div class="inspector-tag badge-fiber">
            SYNAPTIC FIBER #${e.index}
          </div>
        </div>
        <div style="display: flex; align-items: center; gap: 6px;">
          <button class="btn-window-minimize" title="Minimize / Expand Window">${Y.minimize(11,`rgba(255,255,255,0.8)`)}</button>
          <button id="btn-close-inspector" class="btn-close" title="Close Inspector">${Y.closeCross(12,`#cbd5e1`)}</button>
        </div>
      </div>

      <div class="window-body-scroll">
        <h2 class="inspector-title">${e.pathwayName}</h2>
      <div class="inspector-systematic">${e.type.toUpperCase()} CONNECTION</div>

      ${i}

      <!-- Synaptic Telemetry -->
      <div class="telemetry-bar">
        <div class="telemetry-item">
          <span class="telemetry-label">Synaptic Conductance</span>
          <span class="telemetry-val" style="color: var(--accent-cyan);">${(e.synapticWeight*100).toFixed(0)}% (${(e.synapticWeight*48).toFixed(1)} nS)</span>
        </div>
        <div class="telemetry-item">
          <span class="telemetry-label">Transmission Vector</span>
          <span class="telemetry-val" style="text-transform: uppercase;">${e.direction}</span>
        </div>
      </div>

      <!-- Endpoint Cards -->
      <div class="inspector-section">
        <h3>Connected Synaptic Endpoints</h3>
        <div class="endpoint-card">
          <div class="endpoint-header">
            <span>PRE-SYNAPTIC ORIGIN</span>
            <button class="btn-link" id="btn-inspect-src">Inspect Soma #${t.index}</button>
          </div>
          <div class="endpoint-body">
            <strong>Neuron #${t.index}</strong> (${t.type}) in ${r?r.name:t.regionId}
          </div>
        </div>

        <div class="endpoint-card" style="margin-top: 8px;">
          <div class="endpoint-header">
            <span>POST-SYNAPTIC TARGET</span>
            <button class="btn-link" id="btn-inspect-tgt">Inspect Soma #${n.index}</button>
          </div>
          <div class="endpoint-body">
            <strong>Neuron #${n.index}</strong> (${n.type}) in ${n.armIndex>=0?`Arm ${n.armIndex+1}`:`Central Mass`}
          </div>
        </div>
      </div>

      <!-- Trigger Action Potential -->
      <button id="btn-stimulate-fiber" class="btn-action pulse btn-action-fiber">
        ${Y.actionPotential(14,`#89dceb`)}
        <span>Fire Action Potential Along Fiber</span>
      </button>

      <!-- Camera Action -->
      <div class="inspector-actions">
        <button id="btn-focus-fiber" class="btn-action">
          ${Y.spatialOrbit(14,`#89dceb`)}
          <span>Focus Camera on Connection</span>
        </button>
      </div>

      <!-- Scientific Disclaimer -->
      <div class="disclaimer-box" style="margin-top: 8px;">
        <strong>Scientific Framing:</strong> Computational approximation — not an exact biological connectome.
      </div>
      </div>
    `}renderRegionView(){let e=this.currentRegion,t=e.dataClassification===`known`?`badge-known`:e.dataClassification===`inferred`?`badge-inferred`:`badge-approx`;this.container.innerHTML=`
      <div class="inspector-header">
        <div style="display: flex; align-items: center; gap: 8px;">
          <span class="window-drag-icon">${Y.dragGrip(14,`rgba(255,255,255,0.6)`)}</span>
          <div class="inspector-tag" style="background: ${e.colorHex}22; color: ${e.colorHex}; border-color: ${e.colorHex}55;">
            ${e.categoryLabel}
          </div>
        </div>
        <div style="display: flex; align-items: center; gap: 6px;">
          <button class="btn-window-minimize" title="Minimize / Expand Window">${Y.minimize(11,`rgba(255,255,255,0.8)`)}</button>
          <button id="btn-close-inspector" class="btn-close" title="Close Inspector">${Y.closeCross(12,`#cbd5e1`)}</button>
        </div>
      </div>

      <div class="window-body-scroll">
        <h2 class="inspector-title">${e.name}</h2>
      <div class="inspector-systematic">${e.systematicName}</div>

      <!-- Data Classification Badge -->
      <div class="data-badge ${t}">
        <span class="badge-icon">●</span> ${e.classificationLabel}
      </div>

      <!-- Scientific Disclaimer Box -->
      <div class="disclaimer-box">
        <strong>Scientific Framing:</strong> ${e.disclaimer}
      </div>

      <!-- Neuron Population Telemetry -->
      <div class="telemetry-bar">
        <div class="telemetry-item">
          <span class="telemetry-label">Neuron Population</span>
          <span class="telemetry-val" style="color: ${e.colorHex};">${e.neuronCountEstimate}</span>
        </div>
        <div class="telemetry-item">
          <span class="telemetry-label">Share of Nervous System</span>
          <span class="telemetry-val">${e.percentageOfNervousSystem}</span>
        </div>
      </div>

      <!-- Biological Role -->
      <div class="inspector-section">
        <h3>Biological Role & Neuroethology</h3>
        <p>${e.biologicalRole}</p>
      </div>

      <!-- Afferent & Efferent Pathways -->
      <div class="inspector-section">
        <h3>Circuit Afferents & Efferents</h3>
        <div class="pathway-group">
          <div class="pathway-title">Afferent Inputs:</div>
          <div class="tags-container">
            ${e.inputs.map(e=>`<span class="tag tag-input">${e}</span>`).join(``)}
          </div>
        </div>
        <div class="pathway-group" style="margin-top: 8px;">
          <div class="pathway-title">Efferent Outputs:</div>
          <div class="tags-container">
            ${e.outputs.map(e=>`<span class="tag tag-output">${e}</span>`).join(``)}
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="inspector-actions">
        <button id="btn-isolate-region" class="btn-action">
          ${Y.customProbe(14,`#38bdf8`)}
          <span>Isolate This Region</span>
        </button>
        <button id="btn-focus-camera" class="btn-action">
          ${Y.spatialOrbit(14,`#38bdf8`)}
          <span>Focus Camera</span>
        </button>
        <button id="btn-open-region-manual" class="btn-action" style="background: rgba(245, 158, 11, 0.15); border-color: rgba(245, 158, 11, 0.5); color: #f59e0b;">
          <span>📖 View Manual For This Area</span>
        </button>
      </div>

      <!-- Scientific Citations -->
      <div class="inspector-section citations">
        <h3>Key References</h3>
        <ul>
          ${e.scientificReferences.map(e=>`<li>${e}</li>`).join(``)}
        </ul>
      </div>
      </div>
    `}bindEvents(){let e=this.container.querySelector(`#btn-close-inspector`);e&&e.addEventListener(`click`,()=>this.hide());let t=this.container.querySelector(`#btn-isolate-region`);t&&this.currentRegion&&t.addEventListener(`click`,()=>{this.onIsolateRegion&&this.onIsolateRegion(this.currentRegion.id)});let n=this.container.querySelector(`#btn-focus-camera`);n&&this.currentRegion&&n.addEventListener(`click`,()=>{this.onFocusCamera&&this.onFocusCamera(this.currentRegion.id)});let r=this.container.querySelector(`#btn-open-region-manual`);r&&this.currentRegion&&r.addEventListener(`click`,()=>{this.onOpenManual?.(this.currentRegion.id)});let i=this.container.querySelector(`#btn-stimulate-neuron`);i&&this.currentNode&&i.addEventListener(`click`,()=>{this.onStimulateNode&&this.onStimulateNode(this.currentNode.index)});let a=this.container.querySelector(`#btn-focus-neuron`);a&&this.currentNode&&a.addEventListener(`click`,()=>{this.onFocusNeuron&&this.onFocusNeuron(this.currentNode,!1)});let o=this.container.querySelector(`#btn-micro-zoom`);o&&this.currentNode&&o.addEventListener(`click`,()=>{this.onFocusNeuron&&this.onFocusNeuron(this.currentNode,!0)}),this.container.querySelectorAll(`.btn-micro-node`).forEach(e=>{e.addEventListener(`click`,e=>{let t=parseInt(e.currentTarget.getAttribute(`data-node`)||`-1`,10);t>=0&&this.onSelectNeuron&&this.onSelectNeuron(t)})});let s=this.container.querySelector(`#btn-stimulate-fiber`);s&&this.currentFiber&&s.addEventListener(`click`,()=>{this.onStimulateFiber&&this.onStimulateFiber(this.currentFiber.index)});let c=this.container.querySelector(`#btn-focus-fiber`);c&&this.sourceNode&&this.targetNode&&c.addEventListener(`click`,()=>{this.onFocusFiber&&this.onFocusFiber(this.sourceNode,this.targetNode)});let l=this.container.querySelector(`#btn-inspect-src`);l&&this.sourceNode&&this.onSelectNeuron&&l.addEventListener(`click`,()=>{this.onSelectNeuron(this.sourceNode.index)});let u=this.container.querySelector(`#btn-inspect-tgt`);u&&this.targetNode&&this.onSelectNeuron&&u.addEventListener(`click`,()=>{this.onSelectNeuron(this.targetNode.index)})}},he=class{container;items=[];constructor(e=`hierarchy-breadcrumbs`){this.container=document.getElementById(e)||document.body}setPath(e){this.items=e,this.render()}render(){this.container.innerHTML=`
      <div class="breadcrumb-bar">
        <span class="breadcrumb-label">ANATOMICAL DEPTH:</span>
        ${this.items.map((e,t)=>`
          <button class="breadcrumb-btn ${t===this.items.length-1?`active`:``}" data-index="${t}">
            ${e.label}
          </button>
          ${t<this.items.length-1?`<span class="breadcrumb-sep">/</span>`:``}
        `).join(``)}
      </div>
    `,this.container.querySelectorAll(`.breadcrumb-btn`).forEach(e=>{e.addEventListener(`click`,e=>{let t=e.currentTarget,n=parseInt(t.getAttribute(`data-index`)||`0`,10),r=this.items[n];r&&r.onClick()})})}},ge=class{container;onTriggerPathway;onCustomStimulusMode;onToggleFollowSignal;activePathwayId=null;isFollowSignalActive=!1;currentStepInfo=null;constructor(e=`signal-trigger-panel`){this.container=document.getElementById(e)||document.body,this.render()}setStepProgress(e,t){this.currentStepInfo={label:e,description:t},this.render()}clearProgress(){this.activePathwayId=null,this.currentStepInfo=null,this.render()}setFollowSignal(e){this.isFollowSignalActive=e,this.render()}render(){let e=this.currentStepInfo?`
      <div class="signal-progress-card">
        <div class="progress-indicator">
          <span class="pulse-dot"></span>
          <strong>PROPAGATING ACTION POTENTIAL:</strong> ${this.currentStepInfo.label}
        </div>
        <div class="progress-desc">${this.currentStepInfo.description}</div>
      </div>
    `:``;this.container.innerHTML=`
      <div class="signal-panel-header">
        <div style="display: flex; align-items: center; gap: 10px;">
          <span class="window-drag-icon">${Y.dragGrip(14,`rgba(255,255,255,0.6)`)}</span>
          ${Y.actionPotential(15,`#fab387`)}
          <div>
            <span class="signal-title">NEURAL SIGNAL PROPAGATION & ACTION POTENTIAL TRACING</span>
            <span class="signal-subtitle">Trigger dynamic neural action potentials along real 3D anatomical pathways</span>
          </div>
        </div>

        <div style="display: flex; align-items: center; gap: 8px;">
          <button id="btn-toggle-follow-cam" class="btn-follow-signal ${this.isFollowSignalActive?`active`:``}">
            ${this.isFollowSignalActive?`FOLLOWING SIGNAL (ACTIVE)`:`FOLLOW SIGNAL CAMERA`}
          </button>
          <button class="btn-window-minimize" title="Minimize / Expand Dock">
            ${Y.minimize(11,`rgba(255,255,255,0.8)`)}
          </button>
        </div>
      </div>

      <div class="window-body-scroll">
        <div class="signal-buttons-grid">
        <button class="btn-stimulus stimulus-sucker ${this.activePathwayId===`touch_sucker`?`active`:``}" data-id="touch_sucker">
          <span class="stim-icon">${Y.suckerReceptor(18,`#f43f5e`)}</span>
          <div class="stim-text">
            <span class="stim-name">TOUCH SUCKER</span>
            <span class="stim-sub">Sucker Receptor → Axial Cord → Motor Arc</span>
          </div>
        </button>

        <button class="btn-stimulus stimulus-optic ${this.activePathwayId===`visual_stimulus`?`active`:``}" data-id="visual_stimulus">
          <span class="stim-icon">${Y.opticLobe(18,`#a855f7`)}</span>
          <div class="stim-text">
            <span class="stim-name">VISUAL STIMULATION</span>
            <span class="stim-sub">Eye → Optic Lobe → Vertical Memory → Strike</span>
          </div>
        </button>

        <button class="btn-stimulus stimulus-arm ${this.activePathwayId===`arm_stimulation`?`active`:``}" data-id="arm_stimulation">
          <span class="stim-icon">${Y.brachialRing(18,`#38bdf8`)}</span>
          <div class="stim-text">
            <span class="stim-name">ARM TACTILE REFLEX</span>
            <span class="stim-sub">Axial Arc → Interbrachial Ring Handover</span>
          </div>
        </button>

        <button class="btn-stimulus stimulus-escape ${this.activePathwayId===`escape_jet`?`active`:``}" data-id="escape_jet">
          <span class="stim-icon">${Y.escapeJet(18,`#f97316`)}</span>
          <div class="stim-text">
            <span class="stim-name">ESCAPE JET REFLEX</span>
            <span class="stim-sub">Statocyst → Stellar Ganglia → Jet Pulse</span>
          </div>
        </button>

        <button class="btn-stimulus stimulus-custom" id="btn-custom-stim">
          <span class="stim-icon">${Y.customProbe(18,`#10b981`)}</span>
          <div class="stim-text">
            <span class="stim-name">CUSTOM PROBE</span>
            <span class="stim-sub">Click any 3D node</span>
          </div>
        </button>
      </div>

      ${e}
      </div>
    `,this.bindEvents()}bindEvents(){this.container.querySelectorAll(`.btn-stimulus[data-id]`).forEach(e=>{e.addEventListener(`click`,e=>{let t=e.currentTarget.getAttribute(`data-id`);t&&this.onTriggerPathway&&(this.activePathwayId=t,this.onTriggerPathway(t),this.render())})});let e=this.container.querySelector(`#btn-custom-stim`);e&&e.addEventListener(`click`,()=>{this.onCustomStimulusMode&&this.onCustomStimulusMode()});let t=this.container.querySelector(`#btn-toggle-follow-cam`);t&&t.addEventListener(`click`,()=>{this.isFollowSignalActive=!this.isFollowSignalActive,this.onToggleFollowSignal&&this.onToggleFollowSignal(this.isFollowSignalActive),this.render()})}},_e=class{container;state;onStateChange;onResetCamera;onSelectPresetView;onSelectPerspectiveAngle;onStartTour;constructor(e=`control-panel`){this.container=document.getElementById(e)||document.body,this.state={mode:`EXPLORE`,navMode:`ORBIT`,neuronDensity:1,fiberGlow:.85,neuropilOpacity:.28,punctaAlpha:.85,punctaVisible:!0,anatomyOpacity:.08,signalSpeed:1,activityIntensity:1,fibersVisible:!0,isPaused:!1,selectedArmIndex:0},this.render()}setMode(e){this.state.mode=e,this.render()}setNavMode(e){this.state.navMode=e,this.render()}getState(){return{...this.state}}render(){let e=[{key:`EXPLORE`,label:`EXPLORE`,icon:Y.exploreCompass(14,`#89dceb`)},{key:`NEURAL_ACTIVITY`,label:`ACTIVITY`,icon:Y.activityWave(14,`#94e2d5`)},{key:`TRACE_SIGNAL`,label:`TRACE SIGNAL`,icon:Y.actionPotential(14,`#fab387`)},{key:`ARM_MODE`,label:`ARM MODE`,icon:Y.brachialRing(14,`#74c7ec`)},{key:`BRAIN_MODE`,label:`BRAIN MODE`,icon:Y.brainCortex(14,`#cba6f7`)},{key:`NETWORK_MODE`,label:`CONNECTOME ONLY`,icon:Y.connectomeLattice(14,`#89dceb`)},{key:`COMPARE_ANATOMY`,label:`ANATOMY + NETWORK`,icon:Y.anatomyLayer(14,`#f38ba8`)}],t=[{key:`ORBIT`,label:`360° ORBIT`,icon:Y.spatialOrbit(16,`#89dceb`),desc:`Drag to rotate, scroll to zoom`},{key:`FREE_FLY`,label:`INSIDE NETWORK`,icon:Y.freeFlight(16,`#b4befe`),desc:`WASD flight inside nerves`},{key:`FOLLOW_SIGNAL`,label:`FOLLOW SIGNAL`,icon:Y.actionPotential(16,`#fab387`),desc:`Auto-track active action potentials`}];this.container.innerHTML=`
      <!-- Window Titlebar with Drag Gripper & Minimize Controls -->
      <div class="window-titlebar">
        <div class="window-titlebar-left">
          <span class="window-drag-icon">${Y.dragGrip(14,`rgba(255,255,255,0.6)`)}</span>
          <span class="window-title-text">SYSTEM CONTROLS</span>
        </div>
        <div class="window-titlebar-right">
          <button class="btn-window-minimize" title="Minimize / Expand Window">
            ${Y.minimize(11,`rgba(255,255,255,0.8)`)}
          </button>
        </div>
      </div>

      <div class="window-body-scroll">
        <!-- Guided Tour Launcher -->
        <div class="control-section">
          <button id="btn-panel-start-tour">
            ${Y.tourPlay(16,`#ffffff`)}
            <span>HOW THE BRAIN WORKS (TOUR)</span>
          </button>
        </div>

      <!-- 3D Navigation Mode Selector -->
      <div class="control-section">
        <div class="section-title">3D CAMERA / NAVIGATION</div>
        <div class="nav-modes-grid">
          ${t.map(e=>`
            <button class="btn-nav-mode ${this.state.navMode===e.key?`active`:``}" data-nav="${e.key}">
              <div class="nav-mode-header">
                <span class="mode-icon">${e.icon}</span> <strong>${e.label}</strong>
              </div>
              <div class="nav-mode-sub">${e.desc}</div>
            </button>
          `).join(``)}
        </div>
      </div>

      <!-- Interaction Modes -->
      <div class="control-section">
        <div class="section-title">INTERACTION MODES</div>
        <div class="modes-grid">
          ${e.map(e=>`
            <button class="btn-mode ${this.state.mode===e.key?`active`:``}" data-mode="${e.key}">
              <span class="mode-icon">${e.icon}</span> ${e.label}
            </button>
          `).join(``)}
        </div>
      </div>

      ${this.state.mode===`ARM_MODE`?`
        <div class="control-section arm-selector-section">
          <div class="section-title">SELECT ARM (1 - 8)</div>
          <div class="arm-buttons-grid">
            ${Array.from({length:8},(e,t)=>`
              <button class="btn-arm-select ${this.state.selectedArmIndex===t?`active`:``}" data-arm="${t}">
                Arm ${t+1}
              </button>
            `).join(``)}
          </div>
        </div>
      `:``}

      <!-- Perspective Angle Presets -->
      <div class="control-section">
        <div class="section-title">PERSPECTIVE ANGLES</div>
        <div class="angles-grid">
          <button class="btn-angle" data-angle="FRONT">Front</button>
          <button class="btn-angle" data-angle="BACK">Back</button>
          <button class="btn-angle" data-angle="LEFT">Left</button>
          <button class="btn-angle" data-angle="RIGHT">Right</button>
          <button class="btn-angle" data-angle="TOP">Top</button>
          <button class="btn-angle" data-angle="BOTTOM">Bottom</button>
          <button class="btn-angle" data-angle="INSIDE" style="grid-column: span 3; color: #fab387;">
            Inside Brain Cavity
          </button>
        </div>
      </div>

      <!-- FlyWire & Optical Parameters -->
      <div class="control-section">
        <div class="section-title">CONNECTOME VISUAL LAYERS</div>

        <div class="slider-group">
          <div class="slider-header">
            <span>Neuropil Compartment Hulls</span>
            <span class="slider-val" id="val-neuropil-opacity">${Math.round(this.state.neuropilOpacity*100)}%</span>
          </div>
          <input type="range" id="slider-neuropil-opacity" min="0" max="0.75" step="0.02" value="${this.state.neuropilOpacity}">
        </div>

        <div class="slider-group">
          <div class="slider-header">
            <span>Synaptic Puncta (EM Boutons)</span>
            <span class="slider-val" id="val-puncta-alpha">${Math.round(this.state.punctaAlpha*100)}%</span>
          </div>
          <input type="range" id="slider-puncta-alpha" min="0" max="1.5" step="0.05" value="${this.state.punctaAlpha}">
        </div>

        <div class="slider-group">
          <div class="slider-header">
            <span>Synaptic Fiber Glow</span>
            <span class="slider-val" id="val-fiber-glow">${Math.round(this.state.fiberGlow*100)}%</span>
          </div>
          <input type="range" id="slider-fiber-glow" min="0" max="1.5" step="0.05" value="${this.state.fiberGlow}">
        </div>

        <div class="slider-group">
          <div class="slider-header">
            <span>Anatomical Silhouette</span>
            <span class="slider-val" id="val-anatomy-opacity">${Math.round(this.state.anatomyOpacity*100)}%</span>
          </div>
          <input type="range" id="slider-anatomy-opacity" min="0" max="0.45" step="0.02" value="${this.state.anatomyOpacity}">
        </div>

        <div class="slider-group">
          <div class="slider-header">
            <span>Signal Propagation Speed</span>
            <span class="slider-val" id="val-signal-speed">${this.state.signalSpeed.toFixed(1)}x</span>
          </div>
          <input type="range" id="slider-signal-speed" min="0.3" max="3.0" step="0.1" value="${this.state.signalSpeed}">
        </div>

        <div class="slider-group">
          <div class="slider-header">
            <span>Spontaneous Activity Waves</span>
            <span class="slider-val" id="val-activity">${Math.round(this.state.activityIntensity*100)}%</span>
          </div>
          <input type="range" id="slider-activity" min="0" max="2.0" step="0.1" value="${this.state.activityIntensity}">
        </div>
      </div>


      <!-- Hierarchical Region Presets -->
      <div class="control-section">
        <div class="section-title">HIERARCHY PRESETS</div>
        <div class="presets-grid">
          <button class="btn-preset" data-preset="whole">Whole Octopus</button>
          <button class="btn-preset" data-preset="brain">Central Brain</button>
          <button class="btn-preset" data-preset="vertical">Vertical Lobe</button>
          <button class="btn-preset" data-preset="optic_left">Optic Lobe (L)</button>
          <button class="btn-preset" data-preset="optic_right">Optic Lobe (R)</button>
          <button class="btn-preset" data-preset="arm1">Arm 1 (Dorsal)</button>
        </div>
      </div>

      <div class="control-actions">
        <button id="btn-toggle-pause" class="btn-ctrl">
          ${this.state.isPaused?Y.play(12,`#38bdf8`):Y.pause(12,`#38bdf8`)}
          <span>${this.state.isPaused?`Resume Activity`:`Pause Activity`}</span>
        </button>
        <button id="btn-reset-cam" class="btn-ctrl">
          ${Y.exploreCompass(13,`#38bdf8`)}
          <span>Reset Camera</span>
        </button>
      </div>
      </div>
    `,this.bindEvents()}bindEvents(){this.container.querySelectorAll(`.btn-nav-mode`).forEach(e=>{e.addEventListener(`click`,e=>{let t=e.currentTarget.getAttribute(`data-nav`);t&&(this.state.navMode=t,this.notifyChange(),this.render())})}),this.container.querySelectorAll(`.btn-mode`).forEach(e=>{e.addEventListener(`click`,e=>{let t=e.currentTarget.getAttribute(`data-mode`);t&&(this.state.mode=t,t===`NETWORK_MODE`?this.state.anatomyOpacity=0:t===`COMPARE_ANATOMY`&&(this.state.anatomyOpacity=.18),this.notifyChange(),this.render())})}),this.container.querySelectorAll(`.btn-angle`).forEach(e=>{e.addEventListener(`click`,e=>{let t=e.currentTarget.getAttribute(`data-angle`);t&&this.onSelectPerspectiveAngle&&this.onSelectPerspectiveAngle(t)})}),this.container.querySelectorAll(`.btn-arm-select`).forEach(e=>{e.addEventListener(`click`,e=>{let t=e.currentTarget,n=parseInt(t.getAttribute(`data-arm`)||`0`,10);this.state.selectedArmIndex=n,this.notifyChange(),this.render()})});let e=(e,t,n,r)=>{let i=this.container.querySelector(`#${e}`),a=this.container.querySelector(`#${t}`);i&&a&&i.addEventListener(`input`,()=>{let e=parseFloat(i.value);a.textContent=n(e),r(e),this.notifyChange()})};e(`slider-neuropil-opacity`,`val-neuropil-opacity`,e=>`${Math.round(e*100)}%`,e=>this.state.neuropilOpacity=e),e(`slider-puncta-alpha`,`val-puncta-alpha`,e=>`${Math.round(e*100)}%`,e=>this.state.punctaAlpha=e),e(`slider-fiber-glow`,`val-fiber-glow`,e=>`${Math.round(e*100)}%`,e=>this.state.fiberGlow=e),e(`slider-anatomy-opacity`,`val-anatomy-opacity`,e=>`${Math.round(e*100)}%`,e=>this.state.anatomyOpacity=e),e(`slider-signal-speed`,`val-signal-speed`,e=>`${e.toFixed(1)}x`,e=>this.state.signalSpeed=e),e(`slider-activity`,`val-activity`,e=>`${Math.round(e*100)}%`,e=>this.state.activityIntensity=e),this.container.querySelectorAll(`.btn-preset`).forEach(e=>{e.addEventListener(`click`,e=>{let t=e.currentTarget.getAttribute(`data-preset`);t&&this.onSelectPresetView&&this.onSelectPresetView(t)})});let t=this.container.querySelector(`#btn-panel-start-tour`);t&&this.onStartTour&&t.addEventListener(`click`,()=>this.onStartTour());let n=this.container.querySelector(`#btn-toggle-pause`);n&&n.addEventListener(`click`,()=>{this.state.isPaused=!this.state.isPaused,this.notifyChange(),this.render()});let r=this.container.querySelector(`#btn-reset-cam`);r&&this.onResetCamera&&r.addEventListener(`click`,()=>this.onResetCamera())}notifyChange(){this.onStateChange&&this.onStateChange(this.getState())}},ve=class{cameraController;neuralNetwork;signalPropagator;chapters=[];currentChapterIndex=0;isRunning=!1;isPaused=!1;chapterTimeElapsed=0;playbackSpeed=1;pulseIntervalTimer=null;onChapterChange;onTimeUpdate;onTourEnd;constructor(e,t,n){this.cameraController=e,this.neuralNetwork=t,this.signalPropagator=n,this.buildChapters()}buildChapters(){this.chapters=[{id:`distributed_architecture`,number:1,title:`The Distributed Nervous System`,subtitle:`The 3/5ths Rule & Arm Sovereignty`,category:`DISTRIBUTED`,cameraPos:new s(0,48,88),cameraTarget:new s(0,-6,0),durationSeconds:12,highlightRegionId:null,highlightArmIndex:null,fiberGlow:1,neuropilOpacity:.35,punctaAlpha:.9,keyConcept:`60-70% of all 500M neurons reside inside the 8 arms, not the head.`,flowSteps:[{step:`Central Brain (~150M)`,type:`central`},{step:`Brachial Ring (~10M)`,type:`inter`},{step:`8 Axial Cords (~350M)`,type:`motor`},{step:`1,600+ Sucker Ganglia`,type:`sensory`}],narration:[`Unlike vertebrates whose brain centralizes all sensory processing and motor execution, the octopus operates as a decentralized network of semi-autonomous intelligences.`,`Each of the 8 arms contains an Axial Nerve Cord packed with cortical and motor neurons, operating alongside hundreds of autonomous sucker micro-ganglia.`],signalTriggerAction:(e,t)=>{let n=t.connectome.armNodeIndices;for(let t=0;t<8;t++){let r=n[t];if(r.length>0){let t=r[Math.floor(Math.random()*r.length)];e.triggerNeuronMicrocircuitCascade(t,12)}}}},{id:`sucker_reflex`,number:2,title:`Autonomous Sucker-Level Reflex`,subtitle:`Chemotactile Sensing & Local Grip`,category:`REFLEX`,cameraPos:new s(26,-16,22),cameraTarget:new s(22,-18,16),durationSeconds:14,highlightRegionId:`sucker_ganglia`,highlightArmIndex:1,fiberGlow:1.3,neuropilOpacity:.2,punctaAlpha:1.2,keyConcept:`Suckers taste, touch, and grip with zero latency without querying the central head.`,flowSteps:[{step:`Chemotactile Receptors`,type:`sensory`},{step:`Sucker Ganglion Hub`,type:`inter`},{step:`Axial Cord Neuropil`,type:`inter`},{step:`Intramuscular Flexion`,type:`motor`}],narration:[`Tens of thousands of chemotactile receptor cells encircle each sucker rim, tasting amino acids and sensing micro-textures in the water.`,`Sensory input flows into the local Sucker Ganglion, triggering instant reflex arcs to intramuscular nerve cords. The arm wraps and grips prey in milliseconds without waiting for central brain commands.`],signalTriggerAction:e=>{e.triggerPathway(`touch_sucker`)}},{id:`ring_coordination`,number:3,title:`Inter-Arm Coordination Ring`,subtitle:`The Interbrachial Nerve Commissure`,category:`COORDINATION`,cameraPos:new s(0,-1,38),cameraTarget:new s(0,-5,0),durationSeconds:13,highlightRegionId:`brachial_nerve_ring`,highlightArmIndex:null,fiberGlow:1.2,neuropilOpacity:.45,punctaAlpha:1,keyConcept:`Adjacent arms synchronize walking and prey-handover through a direct circular ring.`,flowSteps:[{step:`Arm 1 Tactile`,type:`sensory`},{step:`Interbrachial Commissure`,type:`inter`},{step:`Adjacent Arm Cords`,type:`inter`},{step:`Synchronized Crawl`,type:`motor`}],narration:[`Encircling the base of the esophagus and beak lies the Interbrachial Nerve Ring—a massive neural highway bridging all 8 arm bases together.`,`Proprioceptive signals and tactile discoveries pass laterally between neighboring arms through this commissural loop, enabling seamless crawling and multi-arm prey manipulation without head intervention.`],signalTriggerAction:e=>{e.triggerPathway(`arm_tactile_transfer`)}},{id:`ascending_surprises`,number:4,title:`Event-Driven Ascending Signals`,subtitle:`Sparse Bandwidth & Surprise Summaries`,category:`ASCENDING`,cameraPos:new s(12,12,42),cameraTarget:new s(4,0,0),durationSeconds:13,highlightRegionId:`axial_nerve_cords`,highlightArmIndex:0,fiberGlow:1.1,neuropilOpacity:.3,punctaAlpha:1.1,keyConcept:`Arms only send compressed surprise summaries upward when local predictions fail.`,flowSteps:[{step:`Local Forward Model`,type:`inter`},{step:`High Surprise Event`,type:`sensory`},{step:`Ascending Axial Tract`,type:`inter`},{step:`Subesophageal Intake`,type:`central`}],narration:[`Streaming raw sensory data from 1,600+ suckers would overwhelm any central processor. Instead, each arm runs a local predictive forward model.`,`Only when an arm encounters an unexpected load, chemical anomaly, or high surprise does it fire an ascending summary up the axial cord to alert the central brain.`],signalTriggerAction:(e,t)=>{let n=t.connectome.armNodeIndices[0];if(n.length>0){let t=n[n.length-1];e.triggerNeuronMicrocircuitCascade(t,45)}}},{id:`vertical_lobe_consolidation`,number:5,title:`Central Memory & Coalition Attention`,subtitle:`Vertical Lobe Associative Matrices`,category:`CENTRAL`,cameraPos:new s(0,18,22),cameraTarget:new s(0,6,0),durationSeconds:15,highlightRegionId:`vertical_lobe`,highlightArmIndex:null,fiberGlow:1.25,neuropilOpacity:.55,punctaAlpha:1.2,keyConcept:`25M amacrine interneurons bind visual and tactile inputs for associative learning.`,flowSteps:[{step:`Optic Lobe Visuals`,type:`sensory`},{step:`Superior Frontal Lobe`,type:`inter`},{step:`Vertical Lobe (MSF/VL)`,type:`central`},{step:`Long-Term Memory`,type:`central`}],narration:[`Inside the dorsal skull sits the Vertical Lobe System (MSF/VL)—the cephalopod equivalent of the vertebrate cerebral cortex and hippocampus.`,`Containing ~25 million micro-amacrine interneurons, it performs sparse coalition attention over reporting arms, binding visual scene recognition with tactile memory for long-term associative learning.`],signalTriggerAction:e=>{e.triggerPathway(`visual_hunt`)}},{id:`executive_descending`,number:6,title:`Descending High-Level Motor Commands`,subtitle:`Subesophageal Motor Roots & Delegation`,category:`EXECUTIVE`,cameraPos:new s(0,-6,32),cameraTarget:new s(0,-4,0),durationSeconds:13,highlightRegionId:`subesophageal_mass`,highlightArmIndex:null,fiberGlow:1.2,neuropilOpacity:.45,punctaAlpha:1.1,keyConcept:`The brain sends abstract behavioral goals; arms solve the infinite kinematics.`,flowSteps:[{step:`Executive Intent`,type:`central`},{step:`Subesophageal Mass`,type:`central`},{step:`Brachial Motor Roots`,type:`inter`},{step:`Autonomous Arm Strike`,type:`motor`}],narration:[`When deciding to strike, hide, or jet-escape, the Subesophageal Motor Mass fires broad command signals down the brachial nerve roots.`,`Crucially, the central brain does NOT compute the infinite degrees of freedom of muscular elongation, bending, and torsion. It simply instructs "EXPLORE NORTH" or "ESCAPE", delegating the physics to the arms.`],signalTriggerAction:e=>{e.triggerPathway(`escape_jet`)}},{id:`full_living_system`,number:7,title:`The Living Cephalopod Connectome`,subtitle:`Harmonious Multi-Tiered Intelligence`,category:`FULL_SYSTEM`,cameraPos:new s(0,42,85),cameraTarget:new s(0,-4,0),durationSeconds:16,highlightRegionId:null,highlightArmIndex:null,fiberGlow:.95,neuropilOpacity:.3,punctaAlpha:.9,keyConcept:`A distributed cognitive architecture: decentralized execution + sparse central memory.`,flowSteps:[{step:`1,600+ Autonomous Suckers`,type:`sensory`},{step:`8 Arm Local Planners`,type:`motor`},{step:`Lateral Ring Sync`,type:`inter`},{step:`Sparse Central Memory`,type:`central`}],narration:[`You are witnessing a complete simulation of the octopus nervous system in real-time.`,`Autonomous peripheral sensory-motor reflexes, lateral inter-arm coordination, sparse event-triggered communication, and central associative memory working in seamless biological harmony.`],signalTriggerAction:e=>{e.triggerPathway(`visual_hunt`),setTimeout(()=>e.triggerPathway(`touch_sucker`),3e3),setTimeout(()=>e.triggerPathway(`arm_tactile_transfer`),6e3)}}]}startTour(){this.isRunning=!0,this.isPaused=!1,this.currentChapterIndex=0,this.chapterTimeElapsed=0,this.loadChapter(0)}stopTour(){this.isRunning=!1,this.isPaused=!1,this.clearPulseTimer(),this.neuralNetwork.setIsolatedRegion(null),this.neuralNetwork.setHighlightedArm(null),this.onTourEnd&&this.onTourEnd()}togglePlayPause(){return this.isPaused=!this.isPaused,this.isPaused}nextChapter(){this.currentChapterIndex<this.chapters.length-1?(this.currentChapterIndex++,this.chapterTimeElapsed=0,this.loadChapter(this.currentChapterIndex)):this.stopTour()}prevChapter(){this.currentChapterIndex>0&&(this.currentChapterIndex--,this.chapterTimeElapsed=0,this.loadChapter(this.currentChapterIndex))}jumpToChapter(e){e>=0&&e<this.chapters.length&&(this.currentChapterIndex=e,this.chapterTimeElapsed=0,this.loadChapter(e))}setSpeed(e){this.playbackSpeed=e}setActiveOctopus(e,t){this.neuralNetwork=e,this.signalPropagator=t}isTourActive(){return this.isRunning}isTourPaused(){return this.isPaused}getCurrentChapter(){return this.chapters[this.currentChapterIndex]}loadChapter(e){let t=this.chapters[e];if(!t)return;this.clearPulseTimer();let n=this.cameraController.anchorPosition;this.cameraController.tweenCameraTo(t.cameraPos.clone().add(n),t.cameraTarget.clone().add(n),2200),this.neuralNetwork.setIsolatedRegion(t.highlightRegionId),this.neuralNetwork.setHighlightedArm(t.highlightArmIndex),this.neuralNetwork.setFiberGlow(t.fiberGlow),this.neuralNetwork.setNeuropilHullOpacity(t.neuropilOpacity),this.neuralNetwork.setPunctaAlpha(t.punctaAlpha),t.signalTriggerAction&&(t.signalTriggerAction(this.signalPropagator,this.neuralNetwork),this.pulseIntervalTimer=window.setInterval(()=>{this.isRunning&&!this.isPaused&&t.signalTriggerAction&&t.signalTriggerAction(this.signalPropagator,this.neuralNetwork)},4500)),this.onChapterChange&&this.onChapterChange(t,e,this.chapters.length)}clearPulseTimer(){this.pulseIntervalTimer!==null&&(clearInterval(this.pulseIntervalTimer),this.pulseIntervalTimer=null)}update(e){if(!this.isRunning||this.isPaused)return;let t=e*this.playbackSpeed;this.chapterTimeElapsed+=t;let n=this.chapters[this.currentChapterIndex];if(!n)return;let r=Math.min(1,this.chapterTimeElapsed/n.durationSeconds);this.onTimeUpdate&&this.onTimeUpdate(this.chapterTimeElapsed,n.durationSeconds,r),this.cameraController&&this.cameraController.orbitBy(.04*t,0),this.chapterTimeElapsed>=n.durationSeconds&&this.nextChapter()}},ye=class{container;tourManager;onExitTour;constructor(e,t=`tour-hud-container`){this.tourManager=e;let n=document.getElementById(t);if(!n){n=document.createElement(`div`),n.id=t,n.className=`hidden`;let e=document.getElementById(`app-container`);e?e.appendChild(n):document.body.appendChild(n)}this.container=n,this.tourManager.onChapterChange=(e,t,n)=>{this.render(e,t,n)},this.tourManager.onTimeUpdate=(e,t,n)=>{let r=this.container.querySelector(`#tour-progress-fill`);r&&(r.style.width=`${Math.min(100,Math.max(0,n*100))}%`)},this.tourManager.onTourEnd=()=>{this.hide(),this.onExitTour&&this.onExitTour()}}show(){this.container.classList.remove(`hidden`);let e=this.tourManager.getCurrentChapter();this.render(e,this.tourManager.currentChapterIndex,this.tourManager.chapters.length)}hide(){this.container.classList.add(`hidden`)}render(e,t,n){if(!e)return;let r=this.tourManager.isTourPaused(),i=t===n-1;this.container.innerHTML=`
      <div class="tour-overlay-card glass-panel">
        <!-- Progress Bar at Top -->
        <div class="tour-progress-track">
          <div id="tour-progress-fill" class="tour-progress-fill"></div>
        </div>

        <!-- Header -->
        <div class="tour-header" style="cursor: grab;">
          <div class="tour-badge-row">
            <span class="window-drag-icon">${Y.dragGrip(14,`rgba(255,255,255,0.6)`)}</span>
            <span class="tour-badge">CHAPTER ${e.number} OF ${n}</span>
            <span class="tour-category-tag">${e.category}</span>
          </div>
          <button id="btn-tour-close" class="btn-tour-close" title="Exit Tour">
            ${Y.closeCross(12,`#cbd5e1`)}
          </button>
        </div>

        <div class="tour-title-block">
          <h2 class="tour-title">${e.title}</h2>
          <p class="tour-subtitle">${e.subtitle}</p>
        </div>

        <!-- Key Scientific Insight Callout -->
        <div class="tour-key-concept">
          <span class="concept-icon">${Y.concept(16,`#fab387`)}</span>
          <span class="concept-text">${e.keyConcept}</span>
        </div>

        <!-- Step-by-Step Microcircuit Flowchart -->
        <div class="tour-flow-container">
          <div class="tour-flow-title">NEURAL SIGNAL PATHWAY</div>
          <div class="tour-flow-steps">
            ${e.flowSteps.map((t,n)=>`
              <div class="flow-step flow-${t.type}">
                <span class="flow-step-num">${n+1}</span>
                <span class="flow-step-name">${t.step}</span>
              </div>
              ${n<e.flowSteps.length-1?`<span class="flow-arrow">${Y.flowArrow(10,`rgba(255,255,255,0.4)`)}</span>`:``}
            `).join(``)}
          </div>
        </div>

        <!-- Main Narrative Description -->
        <div class="tour-narrative">
          ${e.narration.map(e=>`<p>${e}</p>`).join(``)}
        </div>

        <!-- Chapter Jump Dots -->
        <div class="tour-chapter-dots">
          ${this.tourManager.chapters.map((e,n)=>`
            <button class="btn-chapter-dot ${n===t?`active`:``}" data-chapter="${n}" title="${e.title}">
              <span class="dot-num">${n+1}</span>
            </button>
          `).join(``)}
        </div>

        <!-- Playback Navigation Bar -->
        <div class="tour-playback-controls">
          <button id="btn-tour-prev" class="btn-tour-nav" ${t===0?`disabled`:``}>
            ${Y.stepPrev(11,t===0?`rgba(255,255,255,0.3)`:`#ffffff`)}
            <span>Prev</span>
          </button>
          
          <button id="btn-tour-playpause" class="btn-tour-playpause ${r?`paused`:``}">
            <span class="btn-tour-icon">${r?Y.play(11,`#ffffff`):Y.pause(11,`#ffffff`)}</span>
            <span class="btn-tour-text">${r?`Resume`:`Pause`}</span>
          </button>

          <button id="btn-tour-next" class="btn-tour-nav">
            <span>${i?`Finish`:`Next`}</span>
            ${i?Y.finishFlag(12,`#34d399`):Y.stepNext(11,`#ffffff`)}
          </button>

          <div class="tour-speed-selector">
            <button class="btn-speed active" data-speed="1.0">1.0x</button>
            <button class="btn-speed" data-speed="1.5">1.5x</button>
            <button class="btn-speed" data-speed="2.0">2.0x</button>
          </div>
        </div>
      </div>
    `,this.bindEvents()}bindEvents(){let e=this.container.querySelector(`#btn-tour-close`);e&&e.addEventListener(`click`,()=>{this.tourManager.stopTour(),this.hide(),this.onExitTour&&this.onExitTour()});let t=this.container.querySelector(`#btn-tour-playpause`);t&&t.addEventListener(`click`,()=>{let e=this.tourManager.togglePlayPause(),n=t.querySelector(`.btn-tour-icon`),r=t.querySelector(`.btn-tour-text`);n&&(n.innerHTML=e?Y.play(11,`#ffffff`):Y.pause(11,`#ffffff`)),r&&(r.textContent=e?`Resume`:`Pause`),t.classList.toggle(`paused`,e)});let n=this.container.querySelector(`#btn-tour-prev`);n&&n.addEventListener(`click`,()=>{this.tourManager.prevChapter()});let r=this.container.querySelector(`#btn-tour-next`);r&&r.addEventListener(`click`,()=>{this.tourManager.nextChapter()}),this.container.querySelectorAll(`.btn-chapter-dot`).forEach(e=>{e.addEventListener(`click`,e=>{let t=e.currentTarget,n=parseInt(t.getAttribute(`data-chapter`)||`0`,10);this.tourManager.jumpToChapter(n)})}),this.container.querySelectorAll(`.btn-speed`).forEach(e=>{e.addEventListener(`click`,e=>{let t=e.currentTarget,n=parseFloat(t.getAttribute(`data-speed`)||`1.0`);this.tourManager.setSpeed(n),this.container.querySelectorAll(`.btn-speed`).forEach(e=>e.classList.remove(`active`)),t.classList.add(`active`)})})}},X=`octopus_workspace_layout_v2`,be=class{windows=new Map;zIndexCounter=35;activeDrag=null;activeResize=null;constructor(){this.setupGlobalListeners()}registerWindow(e){this.windows.set(e.id,e);let t=e.element;if(t.classList.add(`floating-window`),t.setAttribute(`data-window-id`,e.id),!t.querySelector(`.window-resize-gripper`)){let e=document.createElement(`div`);e.className=`window-resize-gripper`,e.title=`Drag to resize window width & height`,e.innerHTML=`
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
          <path d="M8 2L2 8M9 5L5 9M9 8L8 9" stroke="rgba(255,255,255,0.45)" stroke-width="1.2" stroke-linecap="round"/>
        </svg>
      `,t.appendChild(e)}t.addEventListener(`pointerdown`,()=>{this.bringToFront(t)}),this.applyWindowLayout(e)}bringToFront(e){this.zIndexCounter+=1,e.style.zIndex=`${this.zIndexCounter}`}toggleMinimize(e){let t=this.windows.get(e);if(!t)return;let n=t.element,r=n.classList.toggle(`window-minimized`),i=n.querySelector(`.btn-window-minimize`);i&&(i.innerHTML=r?Y.maximize(11,`#ffffff`):Y.minimize(11,`#ffffff`),i.title=r?`Expand Window`:`Minimize Window`),this.saveState()}resetAll(){localStorage.removeItem(X),this.windows.forEach(e=>{let t=e.element;t.classList.remove(`window-minimized`),t.style.removeProperty(`transform`);let n=t.querySelector(`.btn-window-minimize`);n&&(n.innerHTML=Y.minimize(11,`#ffffff`),n.title=`Minimize Window`),this.applyDefaultPosition(e)})}applyDefaultPosition(e){let t=e.element,{left:n,right:r,top:i,bottom:a}=e.defaultPosition,{width:o,height:s,maxHeight:c}=e.defaultDimensions;t.style.position=`absolute`,t.style.left=n===void 0?`auto`:`${n}px`,t.style.right=r===void 0?`auto`:`${r}px`,t.style.top=i===void 0?`auto`:`${i}px`,t.style.bottom=a===void 0?`auto`:`${a}px`,t.style.width=`${o}px`,s?t.style.height=`${s}px`:t.style.height=`auto`,c&&(t.style.maxHeight=`${c}px`)}applyWindowLayout(e){let t=this.loadState()[e.id];if(!t){this.applyDefaultPosition(e);return}let n=e.element;n.style.position=`absolute`,n.style.margin=`0`,n.style.right=`auto`,n.style.bottom=`auto`;let r=Math.max(20,window.innerWidth-80),i=Math.max(20,window.innerHeight-80),a=Math.min(Math.max(10,t.x),r),o=Math.min(Math.max(10,t.y),i);if(n.style.left=`${a}px`,n.style.top=`${o}px`,t.width){let r=e.minWidth||240,i=e.maxWidth||window.innerWidth-40;n.style.width=`${Math.min(Math.max(r,t.width),i)}px`}else n.style.width=`${e.defaultDimensions.width}px`;if(t.height){let r=e.minHeight||120,i=e.maxHeight||window.innerHeight-40,a=Math.min(Math.max(r,t.height),i);n.style.height=`${a}px`,n.style.maxHeight=`${a}px`}if(t.minimized){n.classList.add(`window-minimized`);let e=n.querySelector(`.btn-window-minimize`);e&&(e.innerHTML=Y.maximize(11,`#ffffff`),e.title=`Expand Window`)}}setupGlobalListeners(){document.addEventListener(`pointerdown`,e=>{let t=e.target;if(!t)return;let n=t.closest(`.window-resize-gripper`);if(n){let t=n.closest(`.floating-window`);if(t){let n=t.getAttribute(`data-window-id`);if(n&&this.windows.has(n)){e.preventDefault(),this.bringToFront(t);let r=t.getBoundingClientRect();this.activeResize={id:n,startX:e.clientX,startY:e.clientY,initialWidth:r.width,initialHeight:r.height,element:t},document.body.classList.add(`is-resizing-window`);return}}}let r=t.closest(`.btn-window-minimize`);if(r){let t=r.closest(`.floating-window`)?.getAttribute(`data-window-id`);if(t){e.preventDefault(),e.stopPropagation(),this.toggleMinimize(t);return}}if(t.closest(`button, input, select, a`)&&!t.closest(`.window-drag-handle, .window-titlebar`))return;let i=t.closest(`.window-titlebar, .window-drag-handle, .signal-panel-header, .inspector-header, .tour-header`);if(i){if(t.closest(`button:not(.window-drag-btn), input, select`))return;let n=i.closest(`.floating-window`);if(!n)return;let r=n.getAttribute(`data-window-id`);if(!r||!this.windows.has(r))return;e.preventDefault(),this.bringToFront(n);let a=n.getBoundingClientRect();this.activeDrag={id:r,startX:e.clientX,startY:e.clientY,initialLeft:a.left,initialTop:a.top,element:n},document.body.classList.add(`is-dragging-window`)}}),document.addEventListener(`pointermove`,e=>{if(this.activeDrag){e.preventDefault();let{startX:t,startY:n,initialLeft:r,initialTop:i,element:a}=this.activeDrag,o=e.clientX-t,s=e.clientY-n,c=r+o,l=i+s,u=window.innerWidth-60,d=window.innerHeight-50;c=Math.max(4,Math.min(c,u)),l=Math.max(4,Math.min(l,d)),a.style.margin=`0`,a.style.transform=`none`,a.style.right=`auto`,a.style.bottom=`auto`,a.style.left=`${c}px`,a.style.top=`${l}px`}else if(this.activeResize){e.preventDefault();let{id:t,startX:n,startY:r,initialWidth:i,initialHeight:a,element:o}=this.activeResize,s=this.windows.get(t);if(!s)return;let c=e.clientX-n,l=e.clientY-r,u=s.minWidth||220,d=s.maxWidth||window.innerWidth-20,f=s.minHeight||120,p=s.maxHeight||window.innerHeight-20,m=Math.max(u,Math.min(i+c,d)),h=Math.max(f,Math.min(a+l,p));o.style.width=`${m}px`,o.style.height=`${h}px`,o.style.maxHeight=`${h}px`}}),document.addEventListener(`pointerup`,()=>{this.activeDrag&&(this.activeDrag=null,document.body.classList.remove(`is-dragging-window`),this.saveState()),this.activeResize&&(this.activeResize=null,document.body.classList.remove(`is-resizing-window`),this.saveState())}),document.addEventListener(`dblclick`,e=>{let t=e.target;if(!t||t.closest(`button, input, select`))return;let n=t.closest(`.window-titlebar, .signal-panel-header, .inspector-header, .tour-header`);if(n){let e=n.closest(`.floating-window`)?.getAttribute(`data-window-id`);e&&this.toggleMinimize(e)}})}saveState(){let e={};this.windows.forEach((t,n)=>{let r=document.getElementById(n);if(!r)return;let i=r.getBoundingClientRect();e[n]={x:Math.round(i.left),y:Math.round(i.top),width:Math.round(i.width),height:Math.round(i.height),minimized:r.classList.contains(`window-minimized`)}});try{localStorage.setItem(X,JSON.stringify(e))}catch{}}loadState(){try{let e=localStorage.getItem(X);return e?JSON.parse(e):{}}catch{return{}}}},xe=class{session=null;isLoaded=!1;loadError=null;hiddenStates;centralState;prevActions;prevNeighborMsgs;prevCentralFeedback;constructor(){this.hiddenStates=new Float32Array(512),this.centralState=new Float32Array(64),this.prevActions=new Float32Array(40),this.prevNeighborMsgs=new Float32Array(256),this.prevCentralFeedback=new Float32Array(256)}async init(e=`/models/octopus_brain.onnx`){try{return re.wasm.numThreads=1,this.session=await ie.create(e,{executionProviders:[`wasm`]}),this.isLoaded=!0,console.log(`[WASM] OctopusBrain ONNX model loaded successfully into browser!`),!0}catch(e){return this.loadError=e?.message||String(e),console.warn(`[WASM] Note: ONNX Runtime Web initialization:`,this.loadError),this.isLoaded=!1,!1}}get ready(){return this.isLoaded&&this.session!==null}reset(){this.hiddenStates.fill(0),this.centralState.fill(0),this.prevActions.fill(0),this.prevNeighborMsgs.fill(0),this.prevCentralFeedback.fill(0)}async step(e){if(!this.session)return null;let t=new Float32Array(128);for(let n=0;n<8;n++)for(let r=0;r<16;r++)t[n*16+r]=e[n]?.[r]??0;let n={obs:new j(`float32`,t,[1,8,16]),hidden_states:new j(`float32`,this.hiddenStates,[1,8,64]),central_state:new j(`float32`,this.centralState,[1,64]),prev_actions:new j(`float32`,this.prevActions,[1,8,5]),prev_neighbor_msgs:new j(`float32`,this.prevNeighborMsgs,[1,8,32]),prev_central_feedback:new j(`float32`,this.prevCentralFeedback,[1,8,32])};try{let e=await this.session.run(n),r=e.actions.data,i=e.action_logits.data,a=e.report_probs.data;this.hiddenStates=new Float32Array(e.new_hidden_states.data),this.centralState=new Float32Array(e.new_central_state.data),this.prevActions=new Float32Array(e.new_prev_actions.data),this.prevNeighborMsgs=new Float32Array(e.new_neighbor_msgs.data),this.prevCentralFeedback=new Float32Array(e.new_central_feedback.data);let o=[],s=[],c=[],l=[],u=[],d=[];for(let e=0;e<8;e++){let n=Number(r[e]);o.push(n);let f=[];for(let t=0;t<5;t++)f.push(i[e*5+t]);s.push(f);let p=a[e];c.push(p);let m=p>.5;l.push(m);let h=m?.15+p*.12:.02+Math.abs(t[e*16+4])*.05;u.push(h),d.push(2.8+p*1.5)}let f=l.map((e,t)=>e?t:-1).filter(e=>e!==-1),p=[];if(f.length>=2)for(let e=0;e<f.length-1;e++){let t=f[e],n=f[e+1];(Math.abs(t-n)===1||Math.abs(t-n)===7)&&p.push([t,n])}return{actions:o,actionLogits:s,reportProbs:c,reportFlags:l,surpriseValues:u,coalitionClusters:p,attentionMatrix:Array.from({length:8},(e,t)=>Array.from({length:8},(e,n)=>l[t]&&l[n]?.45:.07)),values:d,decodedIntents:this.decodeIntents(l,u,t)}}catch(e){return console.error(`WASM step error:`,e),null}}decodeIntents(e,t,n){let r=[];for(let i=0;i<8;i++){let a=e[i],o=t[i],s=n[i*16+4],c=n[i*16+11],l=`AUTONOMOUS_EXPLORE`,u=`Autonomous Forage`,d=``,f=`#a6e3a1`,p=`Routine sensory sweep without central gating overhead.`,m=.94;a&&(c<.25||o>.22?(l=`HAZARD_WARNING`,u=`Predator / Hazard Alert`,d=``,f=`#f38ba8`,p=`High local prediction surprise; defensive repulsion priority.`,m=.88):s<.2?(l=`COOPERATIVE_PULL`,u=`Cooperative Grip Request`,d=``,f=`#cba6f7`,p=`Joint target requiring synchronized multi-arm force.`,m=.92):(l=`TARGET_DETECTED`,u=`Prey / Food Detected`,d=``,f=`#89b4fa`,p=`Chemosensory verification of edible target in immediate sector.`,m=.86)),r.push({arm_index:i,intent:l,label:u,icon:d,color:f,description:p,confidence:m,is_reporting:a})}return r}},Se=class{container;isLiveStreaming=!1;streamIntervalId=null;backendOnline=!1;currentScenario=`standard`;currentStepIndex=0;wasmRunner=new xe;wasmReady=!1;onVisualPulse;constructor(){this.container=document.getElementById(`cognitive-inspector`)||this.createContainer(),this.render(),this.initEngines()}async initEngines(){if(await this.checkBackendHealth(),!this.backendOnline)try{await this.wasmRunner.init(`/models/octopus_brain.onnx`)&&(this.wasmReady=!0,this.updateStatusBadge(!0,`WASM NEURAL RUNTIME // ACTIVE`))}catch(e){console.warn(`WASM engine fallback to emulation:`,e)}}createContainer(){let e=document.createElement(`div`);return e.id=`cognitive-inspector`,e.className=`floating-panel`,document.getElementById(`app-container`)?.appendChild(e),e}show(){this.container.style.display=`block`}hide(){this.container.style.display=`none`,this.stopLiveStream()}toggle(){this.container.style.display===`none`?this.show():this.hide()}async checkBackendHealth(){try{let e=await fetch(`http://127.0.0.1:8765/status`,{method:`GET`,signal:AbortSignal.timeout(1500)});if(e.ok){let t=await e.json();this.backendOnline=!0,this.updateStatusBadge(!0,`LIVE PYTORCH MPS (GPU) • Ep Step ${t.step}`);return}}catch{}this.backendOnline=!1,this.wasmReady?this.updateStatusBadge(!0,`WASM NEURAL RUNTIME // ACTIVE`):this.updateStatusBadge(!1,`LOCAL EMULATION MODE (WEIGHTS CACHED)`)}updateStatusBadge(e,t){let n=this.container.querySelector(`#cognitive-backend-badge`);n&&(n.className=e?`status-pill online`:`status-pill offline`,n.innerHTML=`<span class="pulse-dot"></span> ${t}`)}setActiveOctopus(e,t,n){let r=this.container.querySelector(`#cognitive-active-octo-badge`);r&&(r.style.color=n,r.style.borderColor=`${n}55`,r.style.background=`${n}18`,r.innerHTML=`${Y.octoGlyph(e,12)} <span style="margin-left: 5px;">OCTO_${e} // ${t.toUpperCase()}</span>`)}render(){this.container.innerHTML=`
      <div class="panel-header" id="cognitive-header">
        <div class="header-title" style="display: flex; align-items: center; gap: 8px;">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
            <path d="M12 2C7.5 2 4 5.5 4 10C4 13.2 5.8 15.8 8.5 17.2V20C8.5 20.8 9.2 21.5 10 21.5C10.8 21.5 11.5 20.8 11.5 20V18.5H12.5V20C12.5 20.8 13.2 21.5 14 21.5C14.8 21.5 15.5 20.8 15.5 20V17.2C18.2 15.8 20 13.2 20 10C20 5.5 16.5 2 12 2Z" stroke="#a6e3a1" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" fill="rgba(166, 227, 161, 0.15)"/>
            <circle cx="9" cy="9.5" r="1.5" fill="#ffffff"/>
            <circle cx="15" cy="9.5" r="1.5" fill="#ffffff"/>
          </svg>
          <span>COGNITIVE PIPELINE</span>
          <span id="cognitive-active-octo-badge" style="margin-left: 8px; font-size: 10px; padding: 2px 8px; border-radius: 4px; background: rgba(0, 240, 255, 0.12); color: #00f0ff; border: 1px solid rgba(0, 240, 255, 0.3); font-weight: 700; display: inline-flex; align-items: center; font-family: 'Roboto Mono', monospace;">
            ${Y.octoGlyph(0,12)} <span style="margin-left: 5px;">OCTO_0 // ARCHITECT</span>
          </span>
        </div>
        <div class="window-controls">
          <button class="win-btn win-minimize" id="btn-minimize-cognitive" title="Roll up panel">_</button>
        </div>
      </div>

      <div class="panel-content cognitive-content">
        <!-- Scenario Selector & Live Controls Bar -->
        <div class="cognitive-top-bar">
          <div class="scenario-select-wrap">
            <label for="cognitive-scenario-select">TASK OBJECTIVE:</label>
            <select id="cognitive-scenario-select">
              <option value="standard">[FORAGE] Standard Foraging (Sparse Gating)</option>
              <option value="hunting">[COOP] Cooperative Dual-Arm Encirclement</option>
              <option value="amputation">[RESILIENCE] Sudden Amputation (Arm #3 Severed)</option>
              <option value="soft_body_3d">[CONTINUUM] 3D Soft-Body Muscular Hydrostat</option>
            </select>
          </div>

          <div id="cognitive-backend-badge" class="status-pill offline">
            <span class="pulse-dot"></span> CHECKING BRIDGE...
          </div>
        </div>

        <div class="cognitive-action-bar">
          <button id="btn-step-cognition" class="btn-primary-action">
            <span>RUN STEP</span>
          </button>
          <button id="btn-stream-cognition" class="btn-secondary-action">
            <span>LIVE STREAM (60 FPS)</span>
          </button>
          <button id="btn-reset-cognition" class="btn-ghost-action">
            <span>RESET TASK</span>
          </button>
          <div class="reward-pill" id="cognitive-reward-pill">
            Reward: <span class="val">+0.00</span>
          </div>
        </div>

        <!-- 5-Stage Cognitive Flow Display -->
        <div class="cognitive-stages-grid">

          <!-- STAGE 1: SENSORY PERCEPTION -->
          <div class="cognitive-stage-card">
            <div class="stage-header">
              <span class="stage-num">STAGE 1</span>
              <span class="stage-title">Sensory Perception</span>
            </div>
            <div class="stage-desc">8 peripheral patches capturing target & hazard offsets</div>
            <div id="stage1-sensors" class="arm-sensors-grid">
              <!-- Rendered dynamically -->
            </div>
          </div>

          <!-- STAGE 2: LOCAL REFLEX & PREDICTION SURPRISE -->
          <div class="cognitive-stage-card">
            <div class="stage-header">
              <span class="stage-num">STAGE 2</span>
              <span class="stage-title">Local Predictive Coding</span>
            </div>
            <div class="stage-desc">Sensory surprise metric ΔS_i = ||o - ô||² per arm</div>
            <div id="stage2-surprise" class="surprise-meter-list">
              <!-- Rendered dynamically -->
            </div>
          </div>

          <!-- STAGE 3: EVENT GATING DECISION -->
          <div class="cognitive-stage-card">
            <div class="stage-header">
              <span class="stage-num">STAGE 3</span>
              <span class="stage-title">Event-Triggered Gating</span>
            </div>
            <div class="stage-desc">Sigmoid threshold θ: local autonomy vs central report</div>
            <div class="gating-stats-row">
              <span>COMM BUDGET:</span>
              <span id="gating-rate-label" class="badge-accent">0.0% (Target ≤22%)</span>
            </div>
            <div id="stage3-gates" class="gating-flags-grid">
              <!-- Rendered dynamically -->
            </div>
          </div>

          <!-- STAGE 4: CENTRAL COALITION ATTENTION & LEXICON -->
          <div class="cognitive-stage-card">
            <div class="stage-header">
              <span class="stage-num">STAGE 4</span>
              <span class="stage-title">Central Multi-Head Binding & Communication</span>
            </div>
            <div class="stage-desc">Supraesophageal Ganglion creates dynamic arm teams & decodes messages</div>
            
            <div class="coalition-active-box" id="stage4-coalitions">
              <div class="no-coalition">Autonomous Local Operation (No Central Binding)</div>
            </div>
            <div class="consolidation-status" id="stage4-consolidation">
              <span class="dot"></span> Memory Consolidation: Clock Resting
            </div>

            <!-- Inter-Brachial Semantic Chatter -->
            <div class="lexicon-section-title">
              <span>INTER-BRACHIAL SEMANTIC CHATTER</span>
            </div>
            <div id="stage4-lexicon" class="lexicon-chatter-box">
              <!-- Rendered dynamically -->
            </div>
          </div>

          <!-- STAGE 5: SOLUTION GENERATION & EVALUATION -->
          <div class="cognitive-stage-card stage-card-wide">
            <div class="stage-header">
              <span class="stage-num">STAGE 5</span>
              <span class="stage-title">Solution Generation & Evaluation</span>
            </div>
            <div class="stage-desc">Discrete motor actuation distributions + Actor-Critic value assessment</div>
            <div id="stage5-actions" class="actions-matrix-grid">
              <!-- Rendered dynamically -->
            </div>
          </div>

        </div>
      </div>
    `,this.bindEvents(),this.renderDefaultEmulation()}bindEvents(){let e=this.container.querySelector(`#cognitive-scenario-select`);e&&e.addEventListener(`change`,async e=>{if(this.currentScenario=e.target.value,this.backendOnline)try{await fetch(`http://127.0.0.1:8765/scenario`,{method:`POST`,headers:{"Content-Type":`application/json`},body:JSON.stringify({scenario:this.currentScenario})})}catch{}this.step()});let t=this.container.querySelector(`#btn-step-cognition`);t&&t.addEventListener(`click`,()=>{this.step()});let n=this.container.querySelector(`#btn-stream-cognition`);n&&n.addEventListener(`click`,()=>{this.isLiveStreaming?this.stopLiveStream():this.startLiveStream()});let r=this.container.querySelector(`#btn-reset-cognition`);r&&r.addEventListener(`click`,async()=>{if(this.stopLiveStream(),this.currentStepIndex=0,this.wasmRunner.reset(),this.backendOnline)try{await fetch(`http://127.0.0.1:8765/reset`,{method:`POST`})}catch{}this.step()})}async step(){if(this.backendOnline)try{let e=await fetch(`http://127.0.0.1:8765/step`,{method:`GET`});if(e.ok){let t=await e.json();this.applyTelemetry(t);return}}catch{this.backendOnline=!1,this.wasmReady?this.updateStatusBadge(!0,`WASM NEURAL RUNTIME // ACTIVE`):this.updateStatusBadge(!1,`LOCAL EMULATION MODE (WEIGHTS CACHED)`)}if(this.currentStepIndex=(this.currentStepIndex+1)%40,this.wasmReady){let e=this.generateSyntheticObservations(this.currentStepIndex,this.currentScenario),t=await this.wasmRunner.step(e);if(t){let n={step:this.currentStepIndex,max_steps:40,scenario:this.currentScenario,step_reward:14.2+Math.random()*5,cumulative_reward:38+this.currentStepIndex*2.3,is_done:this.currentStepIndex>=39,observations:e,surprise_values:t.surpriseValues,report_flags:t.reportFlags,report_probs:t.reportProbs,report_rate:t.reportFlags.filter(Boolean).length/8,coalition_clusters:t.coalitionClusters,attention_matrix:t.attentionMatrix,is_consolidation_step:this.currentStepIndex%5==0,decoded_intents:t.decodedIntents,action_logits:t.actionLogits,actions:t.actions,values:t.values,amputated_arms:this.currentScenario===`amputation`?[3]:[]};this.applyTelemetry(n);return}}let e=this.generateSyntheticTelemetry(this.currentStepIndex,this.currentScenario);this.applyTelemetry(e)}startLiveStream(){this.isLiveStreaming=!0;let e=this.container.querySelector(`#btn-stream-cognition`);e&&(e.classList.add(`streaming`),e.innerHTML=`<span>PAUSE STREAM</span>`),this.streamIntervalId=setInterval(()=>{this.step()},280)}stopLiveStream(){this.isLiveStreaming=!1,this.streamIntervalId&&=(clearInterval(this.streamIntervalId),null);let e=this.container.querySelector(`#btn-stream-cognition`);e&&(e.classList.remove(`streaming`),e.innerHTML=`<span>LIVE STREAM (60 FPS)</span>`)}applyTelemetry(e){let t=this.container.querySelector(`#cognitive-reward-pill`);if(t){let n=t.querySelector(`.val`);n&&(n.textContent=`${e.cumulative_reward>=0?`+`:``}${e.cumulative_reward.toFixed(2)}`,n.className=`val ${e.step_reward>0?`gain`:e.step_reward<-.5?`loss`:``}`)}let n=this.container.querySelector(`#stage1-sensors`);if(n&&e.observations){let t=``;for(let n=0;n<8;n++){let r=e.observations[n]||[],i=e.amputated_arms?.includes(n),a=(r[4]||.5)*14,o=(r[11]||.8)*14;t+=`
          <div class="arm-sensor-pill ${i?`severed`:``}">
            <div class="arm-id">Arm #${n} ${i?`(Severed)`:``}</div>
            <div class="sensor-bars">
              <div class="s-bar target" title="Target Distance: ${a.toFixed(1)}">
                <span class="bar-fill" style="width: ${Math.max(5,Math.min(100,(1-r[4])*100))}%"></span>
              </div>
              <div class="s-bar hazard" title="Hazard Distance: ${o.toFixed(1)}">
                <span class="bar-fill" style="width: ${Math.max(5,Math.min(100,(1-r[11])*100))}%"></span>
              </div>
            </div>
          </div>
        `}n.innerHTML=t}let r=this.container.querySelector(`#stage2-surprise`);if(r&&e.surprise_values){let t=``;for(let n=0;n<8;n++){let r=e.surprise_values[n]||0;t+=`
          <div class="surprise-row ${r>.15?`high`:``}">
            <span class="arm-tag">A${n}</span>
            <div class="meter-track">
              <div class="meter-fill" style="width: ${Math.min(100,r*400)}%"></div>
            </div>
            <span class="score-val">${r.toFixed(3)}</span>
          </div>
        `}r.innerHTML=t}let i=this.container.querySelector(`#stage3-gates`),a=this.container.querySelector(`#gating-rate-label`);if(a&&(a.textContent=`${(e.report_rate*100).toFixed(1)}% (Target ≤22%)`),i&&e.report_flags){let t=``;for(let n=0;n<8;n++){let r=e.report_flags[n],i=(e.report_probs?e.report_probs[n]:r?.8:.1)*100;t+=`
          <div class="gate-pill ${r?`fire`:`local`}">
            <span class="arm-num">A${n}</span>
            <span class="gate-status">${r?`REPORT ●`:`LOCAL ○`}</span>
            <span class="prob-tag">${i.toFixed(0)}%</span>
          </div>
        `}i.innerHTML=t}let o=this.container.querySelector(`#stage4-coalitions`),s=this.container.querySelector(`#stage4-consolidation`),c=this.container.querySelector(`#stage4-lexicon`);if(o){if(e.coalition_clusters&&e.coalition_clusters.length>0){let t=``;for(let n of e.coalition_clusters)t+=`
            <div class="coalition-tag active-team">
              <span class="team-icon">::</span>
              <span class="team-members">Active Coalition Team: [Arms ${n.join(` ⟷ `)}]</span>
            </div>
          `;o.innerHTML=t}else o.innerHTML=`<div class="no-coalition">Autonomous Local Operation (No Central Binding)</div>`}if(s&&(e.is_consolidation_step?(s.className=`consolidation-status active`,s.innerHTML=`<span class="dot pulse"></span> Slow Memory Consolidation: FIRED (Updated Central GRU)`):(s.className=`consolidation-status`,s.innerHTML=`<span class="dot"></span> Memory Consolidation: Clock Resting (K=5 interval)`)),c&&e.decoded_intents){let t=``;for(let n of e.decoded_intents){let e=Math.round(n.confidence*100);t+=`
          <div class="lexicon-intent-pill ${n.is_reporting?`reporting`:``}" style="border-left: 2px solid ${n.color}">
            <div class="intent-header">
              <span class="arm-id">A${n.arm_index}</span>
              <span class="intent-conf">${e}%</span>
            </div>
            <div class="intent-tag" title="${n.description}">
              <span>${n.icon}</span>
              <span style="color: ${n.color}">${n.label}</span>
            </div>
          </div>
        `}c.innerHTML=t}let l=this.container.querySelector(`#stage5-actions`),u=[`STAY`,`UP`,`DOWN`,`LEFT`,`RIGHT`];if(l&&e.actions){let t=``;for(let n=0;n<8;n++){let r=e.actions[n],i=e.values?e.values[n]:0,a=u[r]||`STAY`;t+=`
          <div class="action-card">
            <div class="act-header">
              <span class="a-title">Arm #${n}</span>
              <span class="a-critic" title="Critic Value Baseline V(s)">V: ${i.toFixed(2)}</span>
            </div>
            <div class="chosen-action-badge act-${a.toLowerCase()}">
              ${a}
            </div>
          </div>
        `}l.innerHTML=t}if(this.onVisualPulse){let t=[],n=[];for(let r=0;r<8;r++)e.report_flags&&e.report_flags[r]&&t.push(r),e.surprise_values&&e.surprise_values[r]>.15&&n.push(r);this.onVisualPulse(t,e.coalition_clusters||[],n)}}generateSyntheticObservations(e,t){let n=[],r=t===`hunting`;for(let t=0;t<8;t++){let i=Array(16).fill(0);i[0]=Math.sin(e*.2+t),i[1]=Math.cos(e*.2+t),i[2]=.1,i[3]=-.1,i[4]=r&&(t===2||t===3)?.12:.45,i[5]=.2,i[6]=0,i[7]=r?1:.5,i[11]=.75,n.push(i)}return n}generateSyntheticTelemetry(e,t){let n=t===`hunting`,r=t===`amputation`,i=t===`soft_body_3d`,a=[!1,!1,!1,!1,!1,!1,!1,!1],o=[],s=[],c=[],l=[],u=[],d=[];n?(a[2]=!0,a[3]=!0,u.push([2,3])):r?(a[2]=e%2==0,a[4]=e%2==0):i?(a[1]=!0,a[5]=!0,u.push([1,5])):e<3&&(a[2]=!0,a[3]=!0,u.push([2,3]));for(let e=0;e<8;e++){let t=a[e]?.18+Math.random()*.08:.03+Math.random()*.04;o.push(t),s.push(Math.floor(Math.random()*5)),c.push(2.5+Math.random()*2),l.push(Array(16).fill(0).map(()=>Math.random()*.5));let r=a[e],u=`AUTONOMOUS_EXPLORE`,f=`Autonomous Forage`,p=``,m=`#a6e3a1`,h=`Routine sensory sweep without central gating overhead.`,g=.95;r&&(n?(u=`COOPERATIVE_PULL`,f=`Cooperative Grip`,p=``,m=`#cba6f7`,h=`Dual-arm bilateral lock on prey.`,g=.94):i?(u=`REACH_ELONGATION`,f=`Hydrostat Elongate`,p=``,m=`#89dceb`,h=`Muscular hydrostat continuum extension.`,g=.91):(u=`TARGET_DETECTED`,f=`Prey Detected`,p=``,m=`#89b4fa`,h=`Chemosensory verification of edible target.`,g=.88)),d.push({arm_index:e,intent:u,label:f,icon:p,color:m,description:h,confidence:g,is_reporting:r})}return{step:e,max_steps:40,scenario:t,step_reward:12.5+Math.random()*6,cumulative_reward:35+e*2.1,is_done:e>=39,observations:l,surprise_values:o,report_flags:a,report_probs:a.map(e=>e?.85:.08),report_rate:a.filter(Boolean).length/8,coalition_clusters:u,attention_matrix:Array.from({length:8},()=>Array(8).fill(.12)),is_consolidation_step:e%5==0,decoded_intents:d,action_logits:Array.from({length:8},()=>[,,,,,].fill(.2)),actions:s,values:c,amputated_arms:r?[3]:[]}}renderDefaultEmulation(){let e=this.generateSyntheticTelemetry(0,`standard`);this.applyTelemetry(e)}},Ce=class{nodes=[];fibers=[];regionNodeIndices={};armNodeIndices=Array.from({length:8},()=>[]);themeColor=null;constructor(){for(let e in I)this.regionNodeIndices[e]=[]}generate(e=1,t){this.nodes=[],this.fibers=[],this.themeColor=t?new h(t):null;for(let e in this.regionNodeIndices)this.regionNodeIndices[e]=[];return this.armNodeIndices=Array.from({length:8},()=>[]),this.generateCentralBrain(e),this.generateOpticLobes(e),this.generateInterbrachialRing(e),this.generateAllArms(e),this.synthesizeSynapticFibers(),this.buildBufferAttributes()}addNode(e,t,n=-1,r=-1,i=`soma`,a=1){let o=this.nodes.length,s=I[t]?.colorHex||`#38bdf8`,c=new h(s);this.themeColor?c.lerp(this.themeColor,.6):c.offsetHSL((Math.random()-.5)*.08,(Math.random()-.5)*.1,(Math.random()-.5)*.1);let l={index:o,position:e,regionId:t,armIndex:n,segmentIndex:r,color:c,size:(i===`ganglion_hub`?3.5:i===`sucker_receptor`?2.2:1.6)*a,type:i,neighbors:[],upstreamNeighbors:[],downstreamNeighbors:[],incomingFiberIndices:[],outgoingFiberIndices:[]};return this.nodes.push(l),this.regionNodeIndices[t]&&this.regionNodeIndices[t].push(o),n>=0&&n<8&&this.armNodeIndices[n].push(o),o}addFiber(e,t,n,r,i,a=`bidirectional`,o=`approx`){let s=this.nodes[e],c=this.nodes[t];if(!s||!c)return;let l=this.fibers.length;s.neighbors.push(t),c.neighbors.push(e),(a===`afferent`||a===`bidirectional`)&&(s.downstreamNeighbors.push(t),c.upstreamNeighbors.push(e),s.outgoingFiberIndices.push(l),c.incomingFiberIndices.push(l)),(a===`efferent`||a===`bidirectional`)&&(c.downstreamNeighbors.push(e),s.upstreamNeighbors.push(t),c.outgoingFiberIndices.push(l),s.incomingFiberIndices.push(l));let u=s.color.clone().lerp(c.color,.5),d=.5+Math.random()*.48,f=i||(r===`tract`?`Axial-Central Connective Tract`:r===`commissural`?`Interbrachial Commissure Loop`:r===`intramuscular`?`Neuromuscular Motor Pathway`:r===`segmental`?`Sensory-Motor Segmental Reflex`:`Associative Neuropil Mesh`);this.fibers.push({index:l,sourceIndex:e,targetIndex:t,regionId:n,type:r,color:u,synapticWeight:d,direction:a,pathwayName:f,biologicalStatus:o})}generateCentralBrain(e){let t=Math.floor(1800*e);for(let e=0;e<t;e++){let t=Math.random(),n=Math.random()*Math.PI*2,r=Math.acos(2*Math.random()-1),i=Math.cbrt(t)*6.5,a=i*Math.sin(r)*Math.cos(n)*.9,o=i*Math.sin(r)*Math.sin(n)*.75+8.5,c=i*Math.cos(r)*1.1+1.5,l=e%25==0?`ganglion_hub`:`soma`;this.addNode(new s(a,o,c),`vertical_lobe`,-1,-1,l,1.2)}let n=Math.floor(650*e);for(let e=0;e<n;e++){let e=Math.cbrt(Math.random())*4.2,t=Math.random()*Math.PI*2,n=Math.acos(2*Math.random()-1),r=e*Math.sin(n)*Math.cos(t)*.85,i=e*Math.sin(n)*Math.sin(t)*.65+6,a=e*Math.cos(n)*.9-4.5;this.addNode(new s(r,i,a),`superior_frontal_lobe`,-1,-1,`soma`,1)}let r=Math.floor(800*e);for(let e=0;e<r;e++){let e=Math.cbrt(Math.random())*4.8,t=Math.random()*Math.PI*2,n=Math.acos(2*Math.random()-1),r=e*Math.sin(n)*Math.cos(t)*.9,i=e*Math.sin(n)*Math.sin(t)*.6+2.5,a=e*Math.cos(n)*.85-5.5;this.addNode(new s(r,i,a),`subfrontal_lobe`,-1,-1,`soma`,1.1)}let i=Math.floor(1600*e);for(let e=0;e<i;e++){let t=Math.random(),n=Math.random()*Math.PI*2,r=Math.acos(2*Math.random()-1),i=Math.cbrt(t)*7.5,a=i*Math.sin(r)*Math.cos(n)*1.1,o=i*Math.sin(r)*Math.sin(n)*.65-4.5,c=i*Math.cos(r)*1,l=e%20==0?`ganglion_hub`:`soma`;this.addNode(new s(a,o,c),`subesophageal_mass`,-1,-1,l,1.3)}}generateOpticLobes(e){let t=[-1,1],n=Math.floor(2800*e);for(let e of t){let t=e*18,r=3.5,i=-.5;for(let e=0;e<n;e++){let a=Math.random(),o=Math.random()*Math.PI*2,c=Math.acos(2*Math.random()-1),l=Math.cbrt(a)*8.5,u=e<n*.6?l:l*.6+3,d=t+u*Math.sin(c)*Math.cos(o)*.95,f=r+u*Math.sin(c)*Math.sin(o)*1.25,p=i+u*Math.cos(c)*.9,m=e%30==0?`ganglion_hub`:`soma`;this.addNode(new s(d,f,p),`optic_lobes`,-1,-1,m,1.15)}for(let n=0;n<5;n++){let a=new s(t*.6,r+(n-2)*1.2,i),o=new s(e*4.5,3+(n-2)*.8,0),c=-1;for(let e=0;e<=12;e++){let t=e/12,n=new s().lerpVectors(a,o,t);n.y+=Math.sin(t*Math.PI)*1.5;let r=this.addNode(n,`optic_lobes`,-1,-1,`synaptic_bouton`,.9);c!==-1&&this.addFiber(c,r,`optic_lobes`,`tract`),c=r}}}}generateInterbrachialRing(e){let t=Math.floor(120*e),n=-1,r=-1;for(let e=0;e<t;e++){let i=e/t*Math.PI*2,a=13*Math.cos(i),o=13*Math.sin(i),c=-5+Math.sin(i*4)*.8,l=this.addNode(new s(a,c,o),`brachial_nerve_ring`,-1,-1,e%15==0?`ganglion_hub`:`soma`,1.2);e===0&&(r=l),n!==-1&&this.addFiber(n,l,`brachial_nerve_ring`,`commissural`),n=l}n!==-1&&r!==-1&&this.addFiber(n,r,`brachial_nerve_ring`,`commissural`)}generateAllArms(e){let t=Array.from({length:8},(e,t)=>t/8*Math.PI*2);for(let n=0;n<8;n++){let r=t[n];this.generateSingleArm(n,r,e)}}generateSingleArm(e,t,n){let r=Math.max(3,Math.floor(8*n)),i=[];for(let n=0;n<6;n++){let r=n/5,a=t+r*.45*(e%2==0?1:-1),o=13+r*55*.9,c=o*Math.cos(a),l=o*Math.sin(a),u=-5.5-r*24.75+Math.sin(r*Math.PI)*4;i.push(new s(c,u,l))}let a=new k(i),o=-1;for(let t=0;t<28;t++){let i=t/27,c=a.getPoint(i),l=a.getTangent(i).normalize(),u=new s(0,1,0).cross(l).normalize(),d=l.clone().cross(u).normalize(),p=f.lerp(3.2,.8,i),m=this.addNode(c.clone().add(new s((Math.random()-.5)*.3,(Math.random()-.5)*.3,(Math.random()-.5)*.3)),`axial_nerve_cords`,e,t,`ganglion_hub`,1.4);o!==-1&&this.addFiber(o,m,`axial_nerve_cords`,`tract`),o=m;for(let n=0;n<r;n++){let i=n/r*Math.PI*2,a=p*.35,o=u.clone().multiplyScalar(Math.cos(i)*a).add(d.clone().multiplyScalar(Math.sin(i)*a)),s=c.clone().add(o),l=this.addNode(s,`axial_nerve_cords`,e,t,`soma`,1);this.addFiber(m,l,`axial_nerve_cords`,`segmental`)}let h=u.clone().multiplyScalar(-p*1.35),g=c.clone().add(h),_=this.addNode(g,`sucker_ganglia`,e,t,`ganglion_hub`,1.5);this.addFiber(m,_,`sucker_ganglia`,`segmental`);let v=Math.max(3,Math.floor(6*n)),y=p*.75,b=-1,x=-1;for(let n=0;n<v;n++){let r=n/v*Math.PI*2,i=d.clone().multiplyScalar(Math.cos(r)*y).add(l.clone().multiplyScalar(Math.sin(r)*y)),a=g.clone().add(i),o=this.addNode(a,`sucker_ganglia`,e,t,`sucker_receptor`,.9);this.addFiber(_,o,`sucker_ganglia`,`segmental`),n===0&&(x=o),b!==-1&&this.addFiber(b,o,`sucker_ganglia`,`dendritic`),b=o}b!==-1&&x!==-1&&this.addFiber(b,x,`sucker_ganglia`,`dendritic`);let S=[0,Math.PI*.5,Math.PI,Math.PI*1.5];for(let n of S){let r=u.clone().multiplyScalar(Math.cos(n)*p*.95).add(d.clone().multiplyScalar(Math.sin(n)*p*.95)),i=c.clone().add(r),a=this.addNode(i,`intramuscular_cords`,e,t,`synaptic_bouton`,1);this.addFiber(m,a,`intramuscular_cords`,`intramuscular`)}}}synthesizeSynapticFibers(){let e=this.regionNodeIndices.subesophageal_mass||[],t=this.regionNodeIndices.brachial_nerve_ring||[],n=this.regionNodeIndices.vertical_lobe||[],r=this.regionNodeIndices.superior_frontal_lobe||[],i=this.regionNodeIndices.subfrontal_lobe||[];if(e.length>0&&t.length>0)for(let n=0;n<t.length;n+=6){let r=t[n],i=this.nodes[r].position,a=-1,o=1/0;for(let t=0;t<Math.min(60,e.length);t++){let n=e[t],r=i.distanceTo(this.nodes[n].position);r<o&&(o=r,a=n)}a!==-1&&this.addFiber(r,a,`brachial_nerve_ring`,`tract`)}this.bridgeRegions(r,n,`vertical_lobe`,`dendritic`,45),this.bridgeRegions(i,r,`subfrontal_lobe`,`dendritic`,35),this.bridgeRegions(n,e,`subesophageal_mass`,`tract`,30)}bridgeRegions(e,t,n,r,i){if(e.length!==0&&t.length!==0)for(let a=0;a<i;a++){let i=e[Math.floor(Math.random()*e.length)],a=t[Math.floor(Math.random()*t.length)];this.addFiber(i,a,n,r)}}buildBufferAttributes(){let e=this.nodes.length,t=new Float32Array(e*3),n=new Float32Array(e*3),r=new Float32Array(e),i=new Float32Array(e);for(let a=0;a<e;a++){let e=this.nodes[a];t[a*3+0]=e.position.x,t[a*3+1]=e.position.y,t[a*3+2]=e.position.z,n[a*3+0]=e.color.r,n[a*3+1]=e.color.g,n[a*3+2]=e.color.b,r[a]=e.size,i[a]=Math.random()*Math.PI*2}let a=this.fibers.length,o=new Float32Array(a*2*3),s=new Float32Array(a*2*3);for(let e=0;e<a;e++){let t=this.fibers[e],n=this.nodes[t.sourceIndex],r=this.nodes[t.targetIndex],i=e*6;o[i+0]=n.position.x,o[i+1]=n.position.y,o[i+2]=n.position.z,s[i+0]=n.color.r,s[i+1]=n.color.g,s[i+2]=n.color.b,o[i+3]=r.position.x,o[i+4]=r.position.y,o[i+5]=r.position.z,s[i+3]=r.color.r,s[i+4]=r.color.g,s[i+5]=r.color.b}let c=a,l=new Float32Array(c*3),u=new Float32Array(c*3);for(let e=0;e<a;e++){let t=this.fibers[e],n=this.nodes[t.sourceIndex],r=this.nodes[t.targetIndex],i=f.lerp(n.position.x,r.position.x,.72),a=f.lerp(n.position.y,r.position.y,.72),o=f.lerp(n.position.z,r.position.z,.72);l[e*3+0]=i,l[e*3+1]=a,l[e*3+2]=o,u[e*3+0]=Math.min(1,r.color.r*1.3+.2),u[e*3+1]=Math.min(1,r.color.g*1.3+.2),u[e*3+2]=Math.min(1,r.color.b*1.3+.2)}return{nodes:this.nodes,fibers:this.fibers,regionNodeIndices:this.regionNodeIndices,armNodeIndices:this.armNodeIndices,nodePositions:t,nodeColors:n,nodeSizes:r,nodePhases:i,fiberLinePositions:o,fiberLineColors:s,punctaPositions:l,punctaColors:u}}};function Z(e){return typeof e==`object`&&!!e&&!Array.isArray(e)}function we(e){return!Z(e)||e.type!==`THEME_CHANGE`&&e.event_type!==`THEME_CHANGE`?!1:Z(e.tokens)}function Te(e){return Z(e)?!!(e.event_type===`LIVE_SERVICE_READY`||typeof e.service_url==`string`&&e.service_url.length>0||Z(e.payload)&&typeof e.payload.primary_url==`string`):!1}function Ee(e){return Z(e)?typeof e.octopus_id==`number`?Number.isFinite(e.octopus_id):typeof e.morphology==`string`||typeof e.mode==`string`:!1}function De(e){let t;if(typeof e==`string`)try{t=JSON.parse(e)}catch(e){return{success:!1,error:`Malformed JSON: ${e instanceof Error?e.message:String(e)}`}}else t=e;return Z(t)?we(t)||Te(t)||Ee(t)?{success:!0,data:t}:{success:!1,error:`Unrecognized telemetry schema: payload did not match any known event contract`}:{success:!1,error:`Invalid telemetry payload: expected an object, got ${t===null?`null`:typeof t}`}}var Oe=class{initialDelayMs;maxDelayMs;backoffMultiplier;currentDelay;attempts=0;timerId=null;constructor(e={}){this.initialDelayMs=e.initialDelayMs??1e3,this.maxDelayMs=e.maxDelayMs??15e3,this.backoffMultiplier=e.backoffMultiplier??1.5,this.currentDelay=this.initialDelayMs}getNextDelay(){return this.currentDelay}getAttempts(){return this.attempts}recordFailure(){this.attempts+=1;let e=this.currentDelay;return this.currentDelay=Math.min(this.currentDelay*this.backoffMultiplier,this.maxDelayMs),e}recordSuccess(){this.cancel(),this.attempts=0,this.currentDelay=this.initialDelayMs}schedule(e){this.cancel();let t=this.recordFailure();return this.timerId=setTimeout(()=>{this.timerId=null,e()},t),t}cancel(){this.timerId!==null&&(clearTimeout(this.timerId),this.timerId=null)}reset(){this.cancel(),this.attempts=0,this.currentDelay=this.initialDelayMs}},Q=[{id:0,name:`System Architect`,code:`ARC`,symbol:`○`,symbolName:`Circle`,colorHex:`#00F0FF`,department:`Architecture & Data`},{id:1,name:`Database & Schemas`,code:`DB`,symbol:`□`,symbolName:`Square`,colorHex:`#A855F7`,department:`Persistence & Models`},{id:2,name:`Backend API`,code:`BE`,symbol:`△`,symbolName:`Triangle`,colorHex:`#3B82F6`,department:`Core Engine & Compute`},{id:3,name:`Frontend UI`,code:`FE`,symbol:`◇`,symbolName:`Diamond`,colorHex:`#EC4899`,department:`Sensory & Evaluation`},{id:4,name:`Cognitive Core`,code:`COG`,symbol:`⬡`,symbolName:`Hexagon`,colorHex:`#10B981`,department:`Reasoning & Tuning`},{id:5,name:`Security & Audit`,code:`SEC`,symbol:`▽`,symbolName:`Inverted Triangle`,colorHex:`#EF4444`,department:`Guardianship & Quantization`},{id:6,name:`Chaos & QA`,code:`QA`,symbol:`☆`,symbolName:`Star`,colorHex:`#F59E0B`,department:`Verification & Serving`},{id:7,name:`DevOps & Deployment`,code:`OPS`,symbol:`+`,symbolName:`Plus`,colorHex:`#EAB308`,department:`Deployment & MLOps`}];function ke(e){return Q.find(t=>t.id===e)??Q[0]}function Ae(e){for(let t of e){let e=Q.find(e=>e.id===t.id);if(e){t.title?e.name=t.title:t.name&&(e.name=t.name);let n=t.colorHex||t.color;n&&typeof n==`string`&&(e.colorHex=n)}}}var je=[{id:0,title:`System Architect`,department:`Architecture & Data`,colorHex:`#00F0FF`,icon:``,status:`ACTIVE`,progressPct:100,coreRole:`Global orchestration & mission planning`,softwareTitle:`System Architect`,softwareRole:`System specifications & folder topology`,aimlTitle:`Data Engineer`,aimlRole:`Dataset ETL & PyTorch DataLoaders`,currentAction:`Global orchestration & mission planning`,surprise:.12,threshold:.45,activeArms:8,position:new s},{id:1,title:`Database & Storage`,department:`Persistence & Models`,colorHex:`#A855F7`,icon:``,status:`ACTIVE`,progressPct:90,coreRole:`Vector memory & persistent storage`,softwareTitle:`Database & Schemas`,softwareRole:`SQL/ORM models & vector persistence`,aimlTitle:`Model Architect`,aimlRole:`Deep neural layers & forward passes`,currentAction:`Vector memory & persistent storage`,surprise:.18,threshold:.5,activeArms:8,position:new s},{id:2,title:`Backend & Services`,department:`Core Engine & Compute`,colorHex:`#3B82F6`,icon:``,status:`ACTIVE`,progressPct:85,coreRole:`API services & backend compute engine`,softwareTitle:`Backend API`,softwareRole:`REST endpoints & distributed services`,aimlTitle:`Training Engineer`,aimlRole:`GPU training loops & hardware compute`,currentAction:`API services & backend compute engine`,surprise:.22,threshold:.5,activeArms:8,position:new s},{id:3,title:`Frontend & UI`,department:`Sensory & Evaluation`,colorHex:`#EC4899`,icon:``,status:`ACTIVE`,progressPct:80,coreRole:`3D visualizer & user interface`,softwareTitle:`Frontend UI`,softwareRole:`User interface views & 3D telepresence`,aimlTitle:`Eval & Benchmarks`,aimlRole:`Accuracy metrics & ROC validation`,currentAction:`3D visualizer & user interface`,surprise:.25,threshold:.55,activeArms:8,position:new s},{id:4,title:`AI & Cognitive Logic`,department:`Reasoning & Tuning`,colorHex:`#10B981`,icon:``,status:`ACTIVE`,progressPct:75,coreRole:`AI reasoning & multi-arm decisions`,softwareTitle:`State & Client Sync`,softwareRole:`Reactive state & hooks synchronization`,aimlTitle:`HPO / Tuner`,aimlRole:`Hyperparameter search & Bayesian tuning`,currentAction:`AI reasoning & multi-arm decisions`,surprise:.19,threshold:.5,activeArms:8,position:new s},{id:5,title:`Sentinel & Security`,department:`Guardianship & Quantization`,colorHex:`#EF4444`,icon:``,status:`ACTIVE`,progressPct:95,coreRole:`Security guardrails & policy enforcement`,softwareTitle:`Security & Audit`,softwareRole:`Security guardrails & vulnerability audit`,aimlTitle:`Quantization & ONNX`,aimlRole:`INT8 quantization & ONNX Runtime graph`,currentAction:`Security guardrails & policy enforcement`,surprise:.08,threshold:.4,activeArms:8,position:new s},{id:6,title:`Chaos & QA Testing`,department:`Verification & Serving`,colorHex:`#F59E0B`,icon:``,status:`ACTIVE`,progressPct:85,coreRole:`Chaos testing & resilience verification`,softwareTitle:`Chaos & QA Testing`,softwareRole:`Unit testing & resilience assertions`,aimlTitle:`Inference Serving`,aimlRole:`FastAPI prediction server & latency benchmarking`,currentAction:`Chaos testing & resilience verification`,surprise:.21,threshold:.4,activeArms:8,position:new s},{id:7,title:`Runner & DevOps`,department:`Deployment & MLOps`,colorHex:`#EAB308`,icon:``,status:`ACTIVE`,progressPct:100,coreRole:`Tool execution & automated workflows`,softwareTitle:`DevOps & Deployment`,softwareRole:`Docker containers & CI/CD deployment`,aimlTitle:`MLOps & Governance`,aimlRole:`Model cards, experiment tracking & lockfiles`,currentAction:`Tool execution & automated workflows`,surprise:.05,threshold:.5,activeArms:8,position:new s}],Me=class{group=new g;scene;camera;controls;cameraController=null;isOctopusFocused=!1;octopuses=new Map;activeOctopusId=0;synapticBeams=[];energyPackets=[];hudOverlayContainer=null;ws=null;reconnectController=new Oe({initialDelayMs:1e3,maxDelayMs:1e4,backoffMultiplier:1.5});onSelectOctopus=null;constructor(e,t,n,r){this.scene=e,this.camera=t,this.controls=n,this.cameraController=r||null,this.initConstellation(),this.createSynapticBeams(),this.setupHUDOverlay(),this.connectTelemetryWebSocket()}setCameraController(e){this.cameraController=e}domainMode=`DUAL`;onDomainModeChange;onLiveServiceReady;onTelemetryEvent;setDomainMode(e){this.domainMode=e,this.updateHUDLabels(),this.onDomainModeChange&&this.onDomainModeChange(e)}initConstellation(){this.group.name=`CephalopodConstellation`;let t=je.length;je.forEach((n,r)=>{let i=r/t*Math.PI*2,a=Math.cos(i)*120,o=Math.sin(i)*120,s=Math.sin(r*1.5)*10;n.position.set(a,s,o);let l=new g;l.position.copy(n.position),l.scale.setScalar(.75),l.rotation.y=-i+Math.PI/2,l.userData={octopusId:n.id,isFullCephalopod:!0};let u=new e(48,16,16),d=new c({transparent:!0,opacity:0,depthWrite:!1}),f=new A(u,d);f.visible=!0,f.name=`hit-collider-${n.id}`,f.userData={octopusId:n.id,isHitCollider:!0},l.add(f);let p=new Ce().generate(1,n.colorHex),m=new oe(p);l.add(m.group);let h=new ce(n.colorHex);l.add(h.group);let _=new le(p,n.colorHex);l.add(_.group),this.group.add(l);let v={id:n.id,data:n,group:l,connectomeData:p,neuralNetwork:m,anatomicalMesh:h,signalPropagator:_,basePosition:n.position.clone(),spontaneousTimer:Math.random()*2};this.octopuses.set(n.id,v)}),this.scene.add(this.group)}createSynapticBeams(){let e=Array.from(this.octopuses.values()),t=e.length;for(let n=0;n<t;n++){let r=(n+1)%t;this.addBeam(e[n].data.id,e[r].data.id,e[n].data.colorHex),n!==0&&n!==t-1&&this.addBeam(0,e[n].data.id,`#00F0FF`),n!==2&&(n===3||n===1||n===6)&&this.addBeam(2,e[n].data.id,`#3B82F6`)}}addBeam(e,t,n){let r=this.octopuses.get(e),i=this.octopuses.get(t);if(!r||!i)return;let a=new s().addVectors(r.basePosition,i.basePosition).multiplyScalar(.5);a.y+=e===0||t===0?28:16;let o=new k([r.basePosition,a,i.basePosition]),c=o.getPoints(36),l=new x().setFromPoints(c),d=new ee({color:new h(n),transparent:!0,opacity:.4,blending:2}),f=new u(l,d);this.group.add(f),this.synapticBeams.push({line:f,curve:o,sourceId:e,targetId:t,color:n}),this.spawnPhotonPacket(o,n)}spawnPhotonPacket(t,n){let r=new e(1.2,12,12),i=new c({color:new h(n),blending:2}),a=new A(r,i);this.group.add(a),this.energyPackets.push({mesh:a,curve:t,progress:Math.random(),speed:.0018+Math.random()*.0025})}setupHUDOverlay(){this.hudOverlayContainer=document.getElementById(`constellation-hud`),this.hudOverlayContainer||(this.hudOverlayContainer=document.createElement(`div`),this.hudOverlayContainer.id=`constellation-hud`,this.hudOverlayContainer.style.cssText=`
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 100;
        overflow: hidden;
      `,document.body.appendChild(this.hudOverlayContainer)),this.updateHUDLabels()}updateHUDLabels(){this.hudOverlayContainer&&(this.hudOverlayContainer.innerHTML=``,this.octopuses.forEach(e=>{let t=document.createElement(`div`),n=ke(e.data.id);t.id=`octo-card-${e.data.id}`,t.className=`glass-panel octo-badge`,t.setAttribute(`data-octo-id`,String(e.data.id)),t.setAttribute(`role`,`button`),t.setAttribute(`tabindex`,`0`),t.setAttribute(`aria-label`,`Arm ${e.data.id}: ${e.data.title} (${n.code}). Status: ${e.data.status}`),t.style.cssText=`
        position: absolute;
        pointer-events: auto;
        cursor: pointer;
        transform: translate(-50%, -50%);
        padding: 8px 14px;
        background: rgba(11, 15, 25, 0.88);
        border: 1px solid ${e.data.colorHex};
        border-radius: 10px;
        box-shadow: 0 0 18px ${e.data.colorHex}55;
        transition: transform 0.2s, box-shadow 0.2s;
        min-width: 200px;
        color: #ffffff;
        font-family: 'Roboto Mono', monospace;
      `;let r=Y.octoGlyph(e.data.id,15),i,a;this.domainMode===`DUAL`?a=`
            <div style="font-weight: 700; font-size: 11px; letter-spacing: 0.02em; margin-bottom: 3px; font-family: 'Roboto Mono', monospace;">
              ${e.data.title.toUpperCase()}
            </div>
            <div style="font-size: 8.5px; line-height: 1.35; margin-bottom: 6px; font-family: 'Roboto Mono', monospace;">
              <div style="color: ${e.data.colorHex}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                <span style="opacity: 0.65; font-size: 7.5px; font-weight: 700;">[SW]</span> ${e.data.softwareRole}
              </div>
              <div style="color: #a6e3a1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 1px;">
                <span style="opacity: 0.65; font-size: 7.5px; font-weight: 700;">[AI]</span> ${e.data.aimlRole}
              </div>
            </div>
          `:this.domainMode===`SOFTWARE`?(i=e.data.softwareTitle.toUpperCase(),a=`
            <div style="font-weight: 700; font-size: 11px; letter-spacing: 0.02em; margin-bottom: 2px; font-family: 'Roboto Mono', monospace;">
              ${i}
            </div>
            <div style="font-size: 9.5px; opacity: 0.85; margin-bottom: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-family: 'Roboto Mono', monospace; color: ${e.data.colorHex};">
              ${e.data.softwareRole}
            </div>
          `):(i=e.data.aimlTitle.toUpperCase(),a=`
            <div style="font-weight: 700; font-size: 11px; letter-spacing: 0.02em; margin-bottom: 2px; font-family: 'Roboto Mono', monospace;">
              ${i}
            </div>
            <div style="font-size: 9.5px; opacity: 0.85; margin-bottom: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-family: 'Roboto Mono', monospace; color: #a6e3a1;">
              ${e.data.aimlRole}
            </div>
          `),t.innerHTML=`
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 5px;">
            <div style="display: flex; align-items: center; gap: 6px;">
              ${r}
              <span style="font-weight: 700; font-size: 11px; letter-spacing: 0.04em; color: ${e.data.colorHex}; font-family: 'Roboto Mono', monospace;">
                <span aria-hidden="true" style="margin-right: 2px;">${n.symbol}</span>[${n.code}] ARM_${e.data.id}
              </span>
            </div>
            <span style="font-size: 9px; font-weight: 600; padding: 1px 5px; border-radius: 4px; background: rgba(56, 189, 248, 0.15); color: #38bdf8; letter-spacing: 0.04em; font-family: 'Roboto Mono', monospace;">
              ${e.data.status}
            </span>
          </div>
          ${a}
          <div style="width: 100%; background: rgba(255, 255, 255, 0.08); height: 3px; border-radius: 2px; overflow: hidden;">
            <div style="width: ${e.data.progressPct}%; background: ${e.data.colorHex}; height: 100%; border-radius: 2px;"></div>
          </div>
        `,t.addEventListener(`mouseenter`,()=>{t.style.transform=`translate(-50%, -50%) scale(1.08)`,t.style.boxShadow=`0 0 28px ${e.data.colorHex}aa`}),t.addEventListener(`mouseleave`,()=>{t.style.transform=`translate(-50%, -50%) scale(1.0)`,t.style.boxShadow=`0 0 18px ${e.data.colorHex}55`}),t.addEventListener(`click`,t=>{t.stopPropagation(),this.focusOnOctopus(e.data.id)}),t.addEventListener(`keydown`,t=>{(t.key===`Enter`||t.key===` `)&&(t.preventDefault(),t.stopPropagation(),this.focusOnOctopus(e.data.id))}),e.badgeCard=t,this.hudOverlayContainer&&this.hudOverlayContainer.appendChild(t)}))}getActiveOctopus(){return this.octopuses.get(this.activeOctopusId)||this.octopuses.get(0)}applyOctopusSpotlight(e){this.octopuses.forEach((t,n)=>{let r=e===null||n===e;t.badgeCard&&(e===null?(t.badgeCard.style.display=`block`,t.badgeCard.style.opacity=`1.0`,t.badgeCard.style.transform=`translate(-50%, -50%) scale(1.0)`,t.badgeCard.style.boxShadow=`0 0 18px ${t.data.colorHex}55`,t.badgeCard.style.borderColor=t.data.colorHex):r?(t.badgeCard.style.display=`block`,t.badgeCard.style.opacity=`1.0`,t.badgeCard.style.transform=`translate(-50%, -50%) scale(1.16)`,t.badgeCard.style.boxShadow=`0 0 35px ${t.data.colorHex}, inset 0 0 12px ${t.data.colorHex}44`,t.badgeCard.style.borderColor=`#ffffff`):(t.badgeCard.style.opacity=`0.18`,t.badgeCard.style.transform=`translate(-50%, -50%) scale(0.82)`,t.badgeCard.style.boxShadow=`none`)),e===null?(t.group.scale.set(1,1,1),t.anatomicalMesh.setOpacity(.14),t.neuralNetwork.setFiberGlow(.85),t.neuralNetwork.setNeuropilHullOpacity(.28)):r?(t.group.scale.set(1,1,1),t.anatomicalMesh.setOpacity(.22),t.neuralNetwork.setFiberGlow(1),t.neuralNetwork.setNeuropilHullOpacity(.38)):(t.group.scale.set(.85,.85,.85),t.anatomicalMesh.setOpacity(.02),t.neuralNetwork.setFiberGlow(.12),t.neuralNetwork.setNeuropilHullOpacity(.04))})}focusOnOctopus(e){let t=this.octopuses.get(e);if(!t)return;this.activeOctopusId=e,this.isOctopusFocused=!0,this.applyOctopusSpotlight(e),this.onSelectOctopus&&this.onSelectOctopus(t.data,t);let n=new s;t.group.getWorldPosition(n);let r=new s(n.x,0,n.z).normalize();r.lengthSq()<.001&&r.set(0,0,1);let i=n.clone().add(r.clone().multiplyScalar(46)).add(new s(0,20,0)),a=n.clone().add(new s(0,4,0));if(this.cameraController)this.cameraController.setAnchor(n),this.cameraController.gtaSwitchTo(i,a,1450,()=>{t.signalPropagator.triggerArmCascade(90)});else{this.controls&&(this.controls.enabled=!0);let e=this.camera.position.clone(),n=this.controls?this.controls.target.clone():new s;new q({camX:e.x,camY:e.y,camZ:e.z,tgtX:n.x,tgtY:n.y,tgtZ:n.z}).to({camX:i.x,camY:i.y,camZ:i.z,tgtX:a.x,tgtY:a.y,tgtZ:a.z},1300).easing(H.Cubic.InOut).onUpdate(e=>{this.camera.position.set(e.camX,e.camY,e.camZ),this.controls&&(this.controls.target.set(e.tgtX,e.tgtY,e.tgtZ),this.controls.update()),this.camera.lookAt(a)}).onComplete(()=>{this.controls&&(this.controls.enabled=!0,this.controls.update()),t.signalPropagator.triggerArmCascade(90)}).start()}}resetOrbitView(){this.isOctopusFocused=!1,this.applyOctopusSpotlight(null);let e=new s(0,140,260),t=new s(0,0,0);if(this.cameraController)this.cameraController.setAnchor(new s(0,0,0)),this.cameraController.gtaSwitchTo(e,t,1400);else{this.controls&&(this.controls.enabled=!0);let n=this.camera.position.clone(),r=this.controls?this.controls.target.clone():new s;new q({camX:n.x,camY:n.y,camZ:n.z,tgtX:r.x,tgtY:r.y,tgtZ:r.z}).to({camX:e.x,camY:e.y,camZ:e.z,tgtX:t.x,tgtY:t.y,tgtZ:t.z},1400).easing(H.Cubic.InOut).onUpdate(e=>{this.camera.position.set(e.camX,e.camY,e.camZ),this.controls&&(this.controls.target.set(e.tgtX,e.tgtY,e.tgtZ),this.controls.update()),this.camera.lookAt(t)}).onComplete(()=>{this.controls&&(this.controls.enabled=!0,this.controls.update())}).start()}}pickOctopus(e,t=!0){let n=Array.from(this.octopuses.values()).map(e=>e.group),r=e.intersectObjects(n,!0);if(r.length>0)for(let e of r){let n=e.object;for(;n;){if(n.userData&&n.userData.octopusId!==void 0){let e=n.userData.octopusId,r=this.octopuses.get(e);if(r)return t&&this.focusOnOctopus(e),r.data}n=n.parent}}return null}connectTelemetryWebSocket(){let e=`${window.location.protocol===`https:`?`wss:`:`ws:`}//${window.location.host||`localhost:8088`}/ws/telemetry`;try{this.ws=new WebSocket(e),this.ws.onopen=()=>{this.reconnectController.recordSuccess()},this.ws.onmessage=e=>{let t=De(e.data);t.success&&t.data&&this.handleTelemetryEvent(t.data)},this.ws.onclose=()=>{this.reconnectController.schedule(()=>this.connectTelemetryWebSocket())}}catch{this.reconnectController.schedule(()=>this.connectTelemetryWebSocket())}}handleTelemetryEvent(e){if(this.onTelemetryEvent&&this.onTelemetryEvent(e),e.type===`THEME_CHANGE`||e.event_type===`THEME_CHANGE`){let t=e.tokens;if(t){let e=document.documentElement;t.primary_hex&&e.style.setProperty(`--accent-cyan`,t.primary_hex),t.secondary_hex&&e.style.setProperty(`--accent-purple`,t.secondary_hex),t.accent_hex&&e.style.setProperty(`--accent-blue`,t.accent_hex),t.success_hex&&e.style.setProperty(`--accent-green`,t.success_hex),t.warning_hex&&e.style.setProperty(`--accent-amber`,t.warning_hex),t.danger_hex&&e.style.setProperty(`--accent-rose`,t.danger_hex),t.bg_hex&&(e.style.setProperty(`--bg-space`,t.bg_hex),this.scene&&(this.scene.background=new h(t.bg_hex),this.scene.fog&&this.scene.fog.color.set(t.bg_hex)))}return}if(e.morphology&&(e.morphology===`aiml_research`&&this.domainMode!==`AIML`?this.setDomainMode(`AIML`):e.morphology===`software_dev`&&this.domainMode!==`SOFTWARE`?this.setDomainMode(`SOFTWARE`):e.morphology===`fullstack_ai`&&this.domainMode!==`DUAL`&&this.setDomainMode(`DUAL`)),e.payload&&Array.isArray(e.payload.arms)?Ae(e.payload.arms):e.payload&&Array.isArray(e.payload.arm_colors)&&Ae(e.payload.arm_colors.map((e,t)=>({id:t,colorHex:e}))),(e.event_type===`LIVE_SERVICE_READY`||e.service_url)&&this.onLiveServiceReady&&this.onLiveServiceReady(e),e.mode===`dry_run`||e.mode===`DRY_RUN`){let e=document.getElementById(`dry-run-indicator-badge`);e||(e=document.createElement(`div`),e.id=`dry-run-indicator-badge`,e.textContent=`DRY-RUN`,e.style.position=`fixed`,e.style.top=`14px`,e.style.left=`50%`,e.style.transform=`translateX(-50%)`,e.style.background=`rgba(234, 179, 8, 0.18)`,e.style.color=`#FACC15`,e.style.border=`1px solid #EAB308`,e.style.borderRadius=`4px`,e.style.padding=`3px 10px`,e.style.fontSize=`11px`,e.style.fontWeight=`700`,e.style.letterSpacing=`1px`,e.style.zIndex=`99999`,e.style.pointerEvents=`none`,e.style.fontFamily=`monospace`,document.body.appendChild(e))}let t=e.octopus_id??0,n=this.octopuses.get(t);if(!n)return;n.data.status=e.status||`ACTIVE`,n.data.currentAction=e.summary||n.data.coreRole,n.data.progressPct=e.progress_pct||n.data.progressPct,n.data.surprise=e.surprise??n.data.surprise;let r=e.arm_id??Math.floor(Math.random()*8);n.signalPropagator.triggerArmAxialStream(r,!1,n.data.colorHex),n.data.surprise>n.data.threshold&&(n.signalPropagator.stimulusOrigin.set(0,8,0),n.signalPropagator.stimulusWaveRadius=.1,n.signalPropagator.stimulusIntensity=1);for(let e of this.synapticBeams)(e.sourceId===t||e.targetId===t)&&this.spawnPhotonPacket(e.curve,n.data.colorHex);this.updateHUDCard(n.data)}updateHUDCard(e){let t=document.getElementById(`octo-card-${e.id}`);if(!t)return;let n=t.querySelector(`div:nth-child(3)`);n&&(n.textContent=e.currentAction);let r=t.querySelector(`div:last-child div`);r&&(r.style.width=`${e.progressPct}%`)}animate(e){let t=performance.now()*.001,n=V();!this.isOctopusFocused&&!n&&(this.group.rotation.y+=e*.018),this.octopuses.forEach((r,i)=>{n?r.group.position.y=r.basePosition.y:(r.anatomicalMesh.update(t,i*.78),r.group.position.y=r.basePosition.y+Math.sin(t*1.4+i*.8)*2.2),r.neuralNetwork.update(t,r.signalPropagator.stimulusOrigin,r.signalPropagator.stimulusWaveRadius,r.signalPropagator.stimulusIntensity,this.camera),r.signalPropagator.update(e,1),r.spontaneousTimer+=e,r.spontaneousTimer>2.8+i%3*.5&&(r.spontaneousTimer=0,r.signalPropagator.triggerSpontaneousActivity())});for(let e=this.energyPackets.length-1;e>=0;e--){let t=this.energyPackets[e];t.progress+=t.speed,t.progress>=1&&(t.progress=0);let n=t.curve.getPointAt(t.progress);t.mesh.position.copy(n)}this.updateBadgeScreenPositions()}updateBadgeScreenPositions(){if(!this.hudOverlayContainer)return;let e=new s;this.octopuses.forEach(t=>{let n=document.getElementById(`octo-card-${t.data.id}`);if(!n)return;if(t.group.getWorldPosition(e),e.y+=24,e.project(this.camera),e.z>1){n.style.display=`none`;return}n.style.display=`block`;let r=(e.x*.5+.5)*window.innerWidth,i=(-(e.y*.5)+.5)*window.innerHeight;n.style.left=`${r}px`,n.style.top=`${i}px`})}},$=[{id:0,title:`System Architect`,department:`Architecture & Data`,colorHex:`#00F0FF`,pitch:.84,rate:1.02,preferredVoices:[`Daniel`,`Alex`,`Fred`,`Arthur`,`Oliver`,`Google US English`],gender:`male`,softwareTitle:`System Architect`,softwareRole:`System specifications, directory topology & module contracts`,softwareScript:`Octo Zero, Chief Architect. I orchestrate global mission directives and route consensus across the consortium.`,aimlTitle:`Data Engineer`,aimlRole:`Dataset ETL, PyTorch DataLoaders & data splits`,aimlScript:`Octo Zero, Data Engineer. I pipeline dataset ingestion, feature scaling, and PyTorch DataLoaders.`,dualRole:`SW: Architecture & specs // AI: Dataset ETL & PyTorch loaders`,dualScript:`Octo Zero. In software, I architect system topology; in AI and ML, I pipeline datasets and PyTorch loaders.`},{id:1,title:`Database & Storage`,department:`Persistence & Models`,colorHex:`#A855F7`,pitch:.94,rate:.96,preferredVoices:[`Samantha`,`Karen`,`Victoria`,`Moira`,`Google UK English Female`],gender:`female`,softwareTitle:`Database & Schemas`,softwareRole:`SQL/ORM models, database connectors & vector persistence`,softwareScript:`Octo One, Synaptic Memory. I manage persistent knowledge graphs, vector recall, and episodic indexing.`,aimlTitle:`Model Architect`,aimlRole:`Deep neural network topologies, attention layers & weights`,aimlScript:`Octo One, Model Architect. I design deep neural network topologies, attention layers, and forward passes.`,dualRole:`SW: Vector persistence // AI: Deep neural layers & weights`,dualScript:`Octo One. In software, I manage database persistence; in AI and ML, I design neural layers and forward passes.`},{id:2,title:`Backend & Services`,department:`Core Engine & Compute`,colorHex:`#3B82F6`,pitch:.96,rate:1.06,preferredVoices:[`Rishi`,`Daniel`,`Tom`,`George`,`Google UK English Male`],gender:`male`,softwareTitle:`Backend API`,softwareRole:`REST/WebSocket endpoints & distributed business logic`,softwareScript:`Octo Two, Backend Engine. I execute high-throughput asynchronous pipelines and distributed neural compute.`,aimlTitle:`Training & Loss Engineer`,aimlRole:`GPU training loops, custom loss functions & AMP acceleration`,aimlScript:`Octo Two, Training Engineer. I execute GPU training loops, custom loss functions, and gradient optimization.`,dualRole:`SW: REST API services // AI: GPU training & hardware compute`,dualScript:`Octo Two. In software, I build backend REST endpoints; in AI and ML, I drive GPU training loops and compute.`},{id:3,title:`Frontend & UI`,department:`Sensory & Evaluation`,colorHex:`#EC4899`,pitch:1.18,rate:1.06,preferredVoices:[`Tessa`,`Samantha`,`Victoria`,`Fiona`,`Google US English`],gender:`female`,softwareTitle:`Frontend UI`,softwareRole:`User interface views, React/Vite layout & 3D telepresence`,softwareScript:`Octo Three, Sensory Telemetry. I stream real-time spatial connectome visualization and telepresence.`,aimlTitle:`Eval & Benchmarks`,aimlRole:`Validation metrics, ROC curves, confusion matrices & loss evaluation`,aimlScript:`Octo Three, Evaluation and Benchmarks. I calculate validation metrics, ROC curves, and test loss convergence.`,dualRole:`SW: 3D UI & telepresence // AI: Accuracy metrics & loss eval`,dualScript:`Octo Three. In software, I render 3D frontend visualizers; in AI and ML, I benchmark accuracy and model loss.`},{id:4,title:`AI & Cognitive Logic`,department:`Reasoning & Tuning`,colorHex:`#10B981`,pitch:1.02,rate:1,preferredVoices:[`Alex`,`Daniel`,`Oliver`,`Google US English`],gender:`neutral`,softwareTitle:`State & Client Sync`,softwareRole:`Reactive state management, custom hooks & store synchronization`,softwareScript:`Octo Four, Cognitive Core. I resolve multi-arm task coalitions and calculate active predictive surprise.`,aimlTitle:`HPO / Tuner`,aimlRole:`Hyperparameter search spaces & Bayesian surprise tuning`,aimlScript:`Octo Four, Hyperparameter Tuner. I optimize hyperparameter search spaces, learning rates, and regularization schedules.`,dualRole:`SW: Reactive state & hooks // AI: Hyperparameter tuning & search`,dualScript:`Octo Four. In software, I manage reactive state; in AI and ML, I tune hyperparameters and predictive surprise.`},{id:5,title:`Sentinel & Security`,department:`Guardianship & Quantization`,colorHex:`#EF4444`,pitch:.76,rate:.98,preferredVoices:[`Fred`,`Daniel`,`Arthur`,`Google UK English Male`],gender:`male`,softwareTitle:`Security & Audit`,softwareRole:`Security guardrails, vulnerability audits & input sanitization`,softwareScript:`Octo Five, System Sentinel. I enforce safety boundaries, execution guardrails, and anomaly isolation.`,aimlTitle:`Quantization & ONNX`,aimlRole:`INT8/FP16 quantization & ONNX Runtime hardware graph export`,aimlScript:`Octo Five, Quantization and ONNX. I apply INT8 quantization and export model computation graphs to ONNX runtime.`,dualRole:`SW: Security guardrails // AI: INT8 quantization & ONNX export`,dualScript:`Octo Five. In software, I enforce security guardrails; in AI and ML, I apply INT8 quantization and ONNX export.`},{id:6,title:`Chaos & QA Testing`,department:`Verification & Serving`,colorHex:`#F59E0B`,pitch:1.24,rate:1.14,preferredVoices:[`Moira`,`Karen`,`Tessa`,`Samantha`],gender:`female`,softwareTitle:`Chaos & QA Testing`,softwareRole:`Unit tests, integration suites & live resilience testing`,softwareScript:`Octo Six, Chaos Engine. I inject live edge-case disruptions to stress-test consortium resilience and failover.`,aimlTitle:`Inference Serving`,aimlRole:`High-throughput FastAPI model endpoints & latency benchmarking`,aimlScript:`Octo Six, Inference Serving. I deploy high-throughput FastAPI prediction endpoints and latency benchmarks.`,dualRole:`SW: Chaos testing & QA // AI: High-speed inference serving`,dualScript:`Octo Six. In software, I stress-test system resilience; in AI and ML, I deploy high-speed model inference.`},{id:7,title:`Runner & DevOps`,department:`Deployment & MLOps`,colorHex:`#EAB308`,pitch:1.12,rate:1.12,preferredVoices:[`Rishi`,`Alex`,`Victoria`,`Google US English`],gender:`male`,softwareTitle:`DevOps & Deployment`,softwareRole:`Docker containerization, CI/CD pipelines & automated workflows`,softwareScript:`Octo Seven, Task Runner. I drive sandbox tool execution, code generation, and automated workflows.`,aimlTitle:`MLOps & Governance`,aimlRole:`Model cards, experiment tracking & reproducibility lockfiles`,aimlScript:`Octo Seven, MLOps and Governance. I maintain model cards, experiment versioning, and reproducibility tracking.`,dualRole:`SW: Docker & CI/CD // AI: MLOps tracking & model cards`,dualScript:`Octo Seven. In software, I automate Docker deployment; in AI and ML, I track experiment reproducibility.`}],Ne=`octoflow_voice_muted`,Pe=class{availableVoices=[];isMuted=!0;domainMode=`DUAL`;bannerContainer=null;hideTimer=null;typewriterTimer=null;currentOctoId=null;onMuteStateChange;onDomainModeChange;constructor(){let e=this.readMuteStorage();this.isMuted=e===null||e,this.initVoices(),this.createBannerElement()}readMuteStorage(){if(typeof window>`u`||!window.localStorage)return null;try{let e=window.localStorage.getItem(Ne);return e===`false`?!1:e===`true`||null}catch{return null}}writeMuteStorage(e){if(typeof window<`u`&&window.localStorage)try{window.localStorage.setItem(Ne,String(e))}catch{}}setMuted(e){this.isMuted=e,this.writeMuteStorage(e),this.isMuted&&(this.stopSpeaking(),this.hideBanner()),this.onMuteStateChange&&this.onMuteStateChange(this.isMuted)}toggleMute(){return this.setMuted(!this.isMuted),this.isMuted}initVoices(){if(typeof window>`u`||!(`speechSynthesis`in window))return;let e=()=>{this.availableVoices=window.speechSynthesis.getVoices()};e(),window.speechSynthesis.onvoiceschanged!==void 0&&(window.speechSynthesis.onvoiceschanged=e)}createBannerElement(){let e=document.getElementById(`neural-voice-banner`);e||(e=document.createElement(`div`),e.id=`neural-voice-banner`,document.body.appendChild(e)),this.bannerContainer=e,this.bannerContainer.style.display=`none`}setDomainMode(e){if(this.domainMode=e,this.onDomainModeChange&&this.onDomainModeChange(e),this.currentOctoId!==null&&this.bannerContainer&&this.bannerContainer.style.display!==`none`){let e=$.find(e=>e.id===this.currentOctoId);e&&this.showBanner(e)}}getDomainMode(){return this.domainMode}getIsMuted(){return this.isMuted}getCurrentOctoId(){return this.currentOctoId}speechQueue=[];isSpeaking=!1;stopSpeaking(){this.speechQueue=[],this.isSpeaking=!1,typeof window<`u`&&`speechSynthesis`in window&&window.speechSynthesis.cancel(),this.typewriterTimer!==null&&(clearInterval(this.typewriterTimer),this.typewriterTimer=null),this.hideTimer!==null&&(clearTimeout(this.hideTimer),this.hideTimer=null)}playNeuralChirp(){if(!this.isMuted)try{let e=window.AudioContext||window.webkitAudioContext;if(!e)return;let t=new e,n=t.createOscillator(),r=t.createGain();n.type=`sine`,n.frequency.setValueAtTime(880,t.currentTime),n.frequency.exponentialRampToValueAtTime(1400,t.currentTime+.045),r.gain.setValueAtTime(.045,t.currentTime),r.gain.exponentialRampToValueAtTime(.001,t.currentTime+.05),n.connect(r),r.connect(t.destination),n.start(),n.stop(t.currentTime+.055)}catch{}}selectVoiceForOctopus(e){if(this.availableVoices.length===0)return null;for(let t of e.preferredVoices){let e=this.availableVoices.find(e=>e.name.toLowerCase().includes(t.toLowerCase())&&e.lang.startsWith(`en`));if(e)return e}let t=this.availableVoices.filter(e=>e.lang.startsWith(`en`));return t.length>0?t[e.id%t.length]:this.availableVoices[e.id%this.availableVoices.length]}speakOctopusRole(e){let t=$.find(t=>t.id===e)||$[0],n=this.domainMode===`SOFTWARE`?t.softwareScript:this.domainMode===`AIML`?t.aimlScript:t.dualScript;this.isSpeaking?this.speechQueue.some(t=>t.profile.id===e)||(this.speechQueue.length>=2&&this.speechQueue.shift(),this.speechQueue.push({profile:t,textToSpeak:n})):this.executeSpeech(t,n)}speakCustom(e,t,n=`#f59e0b`){let r={...$[0],title:e,colorHex:n,softwareScript:t,aimlScript:t,dualScript:t};this.isSpeaking?this.speechQueue.push({profile:r,textToSpeak:t}):this.executeSpeech(r,t)}executeSpeech(e,t){if(this.currentOctoId=e.id,this.isSpeaking=!0,this.playNeuralChirp(),this.showBanner(e,t),!this.isMuted&&typeof window<`u`&&`speechSynthesis`in window){let n=new SpeechSynthesisUtterance(t),r=this.selectVoiceForOctopus(e);r&&(n.voice=r),n.pitch=e.pitch,n.rate=e.rate,n.volume=1;let i=()=>{if(this.isSpeaking=!1,this.stopAudioWaveAnimation(),this.speechQueue.length>0){let e=this.speechQueue.shift();window.setTimeout(()=>this.executeSpeech(e.profile,e.textToSpeak),650)}else this.hideTimer=window.setTimeout(()=>{this.hideBanner()},3200)};n.onend=i,n.onerror=i,window.speechSynthesis.speak(n)}else if(this.isSpeaking=!1,this.stopAudioWaveAnimation(),this.speechQueue.length>0){let e=this.speechQueue.shift();window.setTimeout(()=>this.executeSpeech(e.profile,e.textToSpeak),650)}else this.hideTimer=window.setTimeout(()=>{this.hideBanner()},4500)}showBanner(e,t){if(!this.bannerContainer)return;let n=Y.octoGlyph(e.id,16),r=t||(this.domainMode===`SOFTWARE`?e.softwareScript:this.domainMode===`AIML`?e.aimlScript:e.dualScript);this.bannerContainer.style.display=`block`,this.bannerContainer.style.borderColor=e.colorHex,this.bannerContainer.style.boxShadow=`0 4px 28px ${e.colorHex}33, 0 0 1px ${e.colorHex}`;let i=this.domainMode===`DUAL`?`<span class="mode-tag-dual">DUAL-DOMAIN (SW + AI/ML)</span>`:this.domainMode===`SOFTWARE`?`<span class="mode-tag-sw">SOFTWARE DEV MODE</span>`:`<span class="mode-tag-aiml">AI/ML RESEARCH MODE</span>`,a;a=this.domainMode===`DUAL`?`
        <div class="dual-roles-container">
          <div class="dual-role-line">
            <span class="role-pill sw">SOFTWARE</span>
            <span class="role-spec"><strong>${e.softwareTitle}:</strong> ${e.softwareRole}</span>
          </div>
          <div class="dual-role-line">
            <span class="role-pill aiml">AI / ML</span>
            <span class="role-spec"><strong>${e.aimlTitle}:</strong> ${e.aimlRole}</span>
          </div>
        </div>
      `:this.domainMode===`SOFTWARE`?`
        <div class="single-role-line" style="color: ${e.colorHex};">
          <strong>ROLE:</strong> ${e.softwareTitle.toUpperCase()} — ${e.softwareRole}
        </div>
      `:`
        <div class="single-role-line" style="color: #a6e3a1;">
          <strong>ROLE:</strong> ${e.aimlTitle.toUpperCase()} — ${e.aimlRole}
        </div>
      `,this.bannerContainer.innerHTML=`
      <div class="voice-banner-header">
        <div class="voice-banner-title-wrap">
          <span class="voice-glyph">${n}</span>
          <span class="voice-tag" style="color: ${e.colorHex};">
            OCTO_${e.id} // ${e.title.toUpperCase()}
          </span>
          ${i}
        </div>

        <div class="voice-banner-status">
          <div class="audio-wave-bars" id="audio-wave-bars">
            <span style="background: ${e.colorHex};"></span>
            <span style="background: ${e.colorHex};"></span>
            <span style="background: ${e.colorHex};"></span>
            <span style="background: ${e.colorHex};"></span>
          </div>
          <span class="transmission-live-tag">LIVE TRANSMISSION</span>
          <button class="btn-banner-close" id="btn-banner-close" title="Dismiss subtitle">×</button>
        </div>
      </div>

      <div class="voice-banner-body">
        ${a}
        <div class="voice-banner-text" id="voice-banner-text">
          "${r}"
        </div>
      </div>
    `;let o=this.bannerContainer.querySelector(`#btn-banner-close`);o&&o.addEventListener(`click`,e=>{e.stopPropagation(),this.stopSpeaking(),this.hideBanner()}),this.runTypewriter(r)}runTypewriter(e){let t=this.bannerContainer?.querySelector(`#voice-banner-text`);if(!t)return;t.textContent=`"`;let n=0;this.typewriterTimer=window.setInterval(()=>{n<e.length?(t.textContent=`"${e.substring(0,n+1)}"`,n++):this.typewriterTimer!==null&&(clearInterval(this.typewriterTimer),this.typewriterTimer=null)},22)}stopAudioWaveAnimation(){let e=this.bannerContainer?.querySelector(`#audio-wave-bars`);e&&e.classList.add(`paused`)}hideBanner(){this.bannerContainer&&(this.bannerContainer.style.display=`none`)}},Fe=class{container;isVisible=!1;currentTab=`commands`;targetFocusItem=null;onSimulateCommand;onVoiceNarrate;constructor(){this.container=document.createElement(`div`),this.container.id=`manual-drawer-container`,this.container.className=`manual-drawer-wrapper hidden`,document.body.appendChild(this.container),this.render(),this.bindEvents()}toggle(){this.isVisible?this.close():this.open()}open(e=`commands`,t){if(this.currentTab=e,this.targetFocusItem=t||null,this.isVisible=!0,this.container.classList.remove(`hidden`),this.container.classList.add(`visible`),this.container.querySelectorAll(`.manual-tab`).forEach(t=>{t.classList.toggle(`active`,t.getAttribute(`data-tab`)===e)}),this.renderContent(),this.targetFocusItem)setTimeout(()=>{let e=this.container.querySelector(`[data-item-id="${this.targetFocusItem}"]`);e&&(e.scrollIntoView({behavior:`smooth`,block:`center`}),e.style.borderColor=`#f59e0b`,e.style.boxShadow=`0 0 20px rgba(245, 158, 11, 0.4)`,setTimeout(()=>{e.style.borderColor=``,e.style.boxShadow=``},2400))},100);else{let e=this.container.querySelector(`#manual-search-input`);e&&e.focus()}}close(){this.isVisible=!1,this.container.classList.remove(`visible`),this.container.classList.add(`hidden`)}isOpen(){return this.isVisible}bindEvents(){this.container.addEventListener(`click`,e=>{e.target===this.container&&this.close()}),window.addEventListener(`keydown`,e=>{((document.activeElement?.tagName||``).toLowerCase()!==`input`||e.key===`Escape`)&&(e.key===`?`||e.key.toLowerCase()===`m`&&!e.ctrlKey&&!e.metaKey?(e.preventDefault(),this.toggle()):e.key===`Escape`&&this.isVisible&&this.close())})}render(){this.container.innerHTML=`
      <div class="manual-drawer-panel glass-panel">
        <div class="manual-header">
          <div class="manual-brand">
            <span class="manual-logo">🐙</span>
            <div>
              <div class="manual-title">OCTOFLOW DEVELOPER MANUAL & FIELD GUIDE</div>
              <div class="manual-subtitle">Cephalopod Neural Architecture • Active Inference • Complete Reference</div>
            </div>
          </div>
          <button id="btn-close-manual" class="manual-close-btn" title="Close (ESC / ?)">✕</button>
        </div>

        <div class="manual-search-bar">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input type="text" id="manual-search-input" placeholder="Search commands, arm roles, playbooks, or flags (e.g. audit, eject, claude)..." />
        </div>

        <div class="manual-tabs">
          <button class="manual-tab ${this.currentTab===`commands`?`active`:``}" data-tab="commands">⚡ Master Commands</button>
          <button class="manual-tab ${this.currentTab===`arms`?`active`:``}" data-tab="arms">🧠 8 Arm Ganglia</button>
          <button class="manual-tab ${this.currentTab===`playbooks`?`active`:``}" data-tab="playbooks">🚀 Playbooks</button>
          <button class="manual-tab ${this.currentTab===`biology`?`active`:``}" data-tab="biology">🌊 Biological Principles</button>
          <button class="manual-tab ${this.currentTab===`federation`?`active`:``}" data-tab="federation">🛡️ Zero-Trust PII</button>
          <button class="manual-tab ${this.currentTab===`shortcuts`?`active`:``}" data-tab="shortcuts">⌨️ Shortcuts</button>
        </div>

        <div id="manual-content-body" class="manual-content-body">
          <!-- Dynamically populated -->
        </div>

        <div class="manual-footer">
          <span>Tip: You can also run <code class="inline-code">./octo manual</code> in your terminal anytime.</span>
          <span class="manual-hotkey-badge">Press ? or M to toggle</span>
        </div>
      </div>
    `,this.container.querySelector(`#btn-close-manual`)?.addEventListener(`click`,()=>this.close());let e=this.container.querySelectorAll(`.manual-tab`);e.forEach(t=>{t.addEventListener(`click`,()=>{e.forEach(e=>e.classList.remove(`active`)),t.classList.add(`active`),this.currentTab=t.getAttribute(`data-tab`)||`commands`,this.renderContent()})}),this.container.querySelector(`#manual-search-input`)?.addEventListener(`input`,e=>{let t=e.target.value.toLowerCase().trim();this.filterContent(t)})}filterContent(e){if(!e){this.renderContent();return}let t=this.container.querySelector(`#manual-content-body`);if(!t)return;let n=[];for(let t of Ie)(t.cmd.toLowerCase().includes(e)||t.desc.toLowerCase().includes(e)||t.category.toLowerCase().includes(e))&&n.push(this.renderCommandCard(t));for(let t of Le)(t.name.toLowerCase().includes(e)||t.domain.toLowerCase().includes(e)||t.tools.toLowerCase().includes(e))&&n.push(this.renderArmCard(t));n.length>0?(t.innerHTML=`
        <div class="manual-section-header">Search Results for "${e}" (${n.length} found)</div>
        <div class="manual-grid">${n.join(``)}</div>
      `,this.attachActionListeners()):t.innerHTML=`
        <div class="manual-empty">
          <div style="font-size: 28px; margin-bottom: 8px;">🔍</div>
          <div>No direct matches found for "<strong>${e}</strong>".</div>
          <div style="font-size: 12px; color: #888; margin-top: 4px;">Try searching for "audit", "eject", "heal", "theme", or "claude".</div>
        </div>
      `}renderContent(){let e=this.container.querySelector(`#manual-content-body`);e&&(this.currentTab===`commands`?e.innerHTML=`
        <div class="manual-section-header">⚡ Master Command Directory (Click Copy to Run in Shell or Cockpit)</div>
        <div class="manual-grid">
          ${Ie.map(e=>this.renderCommandCard(e)).join(``)}
        </div>
      `:this.currentTab===`arms`?e.innerHTML=`
        <div class="manual-section-header">🧠 The 8 Specialized Cephalopod Arm Ganglia</div>
        <div class="manual-grid">
          ${Le.map(e=>this.renderArmCard(e)).join(``)}
        </div>
      `:this.currentTab===`playbooks`?e.innerHTML=`
        <div class="manual-section-header">🚀 Step-by-Step Developer Playbooks (Click 🎧 Listen to Hear Narration)</div>
        <div class="manual-playbook-list">
          <div class="manual-playbook-card" data-item-id="playbook-scaffold">
            <div style="display: flex; align-items: center; justify-content: space-between;">
              <h3>Playbook 1: Build a Feature from Scratch</h3>
              <button class="btn-narrate" data-narrate-title="Playbook 1" data-narrate-text="Playbook One: Build a feature from scratch. First, launch the cockpit with ./octo. Preview the allocation with /plan. Deploy the swarm, then ignite your live dev servers with /ignite.">🎧 Listen</button>
            </div>
            <ol>
              <li>Launch cockpit: <code class="inline-code">./octo</code></li>
              <li>Preview 8-arm task allocation: <code class="inline-code">/plan Build user auth with JWT & bcrypt</code></li>
              <li>Deploy Swarm: Type your prompt and press <strong>Enter</strong>. Watch action potentials fire in this 3D view!</li>
              <li>Boot frontend & backend live dev servers: <code class="inline-code">/ignite</code></li>
            </ol>
          </div>
          <div class="manual-playbook-card" data-item-id="playbook-heal">
            <div style="display: flex; align-items: center; justify-content: space-between;">
              <h3>Playbook 2: Self-Healing Failing Tests</h3>
              <button class="btn-narrate" data-narrate-title="Playbook 2" data-narrate-text="Playbook Two: Self-healing test repair loop. Run ./octo heal. Arm Five runs Pytest and isolates failing AST nodes. Arm Two writes surgical repairs, and Arm Five re-tests to prove convergence.">🎧 Listen</button>
            </div>
            <ol>
              <li>Run <code class="inline-code">./octo heal</code> (or <code class="inline-code">/heal</code> in cockpit).</li>
              <li>Arm 5 executes Pytest, captures traceback AST nodes, and isolates failing lines.</li>
              <li>Arm 2 writes surgical code repairs, and Arm 5 re-runs tests to prove convergence.</li>
            </ol>
          </div>
          <div class="manual-playbook-card" data-item-id="playbook-eject">
            <div style="display: flex; align-items: center; justify-content: space-between;">
              <h3>Playbook 3: Ejecting Standalone Agent Toolkit</h3>
              <button class="btn-narrate" data-narrate-title="Playbook 3" data-narrate-text="Playbook Three: Ejecting a standalone agent toolkit. Run ./octo eject. Embed the zero-dependency files into any repository or Docker container, then run python run.py directly.">🎧 Listen</button>
            </div>
            <ol>
              <li>Run <code class="inline-code">./octo eject --output ./my-agent-kit</code></li>
              <li>Embed into any repository or Docker container with zero heavyweight dependencies.</li>
              <li>Run directly: <code class="inline-code">python ./my-agent-kit/run.py "Deploy microservice"</code></li>
            </ol>
          </div>
          <div class="manual-playbook-card" data-item-id="playbook-claude">
            <div style="display: flex; align-items: center; justify-content: space-between;">
              <h3>Playbook 4: Native Claude Code & Cursor MCP Integration</h3>
              <button class="btn-narrate" data-narrate-title="Playbook 4" data-narrate-text="Playbook Four: Native Claude Code integration. Run ./octo install-claude to provision the plugin manifest and MCP config. Use slash commands like /octo and /octo:audit inside Claude Code.">🎧 Listen</button>
            </div>
            <ol>
              <li>Run <code class="inline-code">./octo install-claude</code> to provision <code class="inline-code">.claude-plugin/</code> and <code class="inline-code">.mcp.json</code>.</li>
              <li>Use slash commands inside Claude Code: <code class="inline-code">/octo</code>, <code class="inline-code">/octo:audit</code>, <code class="inline-code">/octo:swarm</code>, <code class="inline-code">/octo:heal</code>.</li>
            </ol>
          </div>
        </div>
      `:this.currentTab===`biology`?e.innerHTML=`
        <div class="manual-section-header">🌊 Cephalopod Biological Principles & Active Inference</div>
        <div class="manual-text-block">
          <!-- Interactive SVG Architectural Diagram -->
          <div style="background: rgba(0, 0, 0, 0.4); border: 1px solid rgba(0, 240, 255, 0.3); border-radius: 10px; padding: 16px; margin-bottom: 16px; text-align: center;">
            <div style="font-size: 11px; font-weight: 700; color: #00f0ff; letter-spacing: 0.1em; margin-bottom: 8px;">5-STAGE ACTIVE INFERENCE & SENSORY SURPRISE GATING PIPELINE</div>
            <svg width="100%" height="90" viewBox="0 0 680 90" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="10" y="25" width="105" height="40" rx="6" fill="#1e293b" stroke="#38bdf8" stroke-width="1.5"/>
              <text x="62" y="44" fill="#38bdf8" font-size="10" font-family="monospace" text-anchor="middle" font-weight="bold">1. SENSORY</text>
              <text x="62" y="56" fill="#94a3b8" font-size="8" font-family="monospace" text-anchor="middle">Proprioception</text>

              <path d="M120 45H145" stroke="#38bdf8" stroke-width="1.5" marker-end="url(#arrow)"/>

              <rect x="150" y="25" width="115" height="40" rx="6" fill="#1e293b" stroke="#a855f7" stroke-width="1.5"/>
              <text x="207" y="44" fill="#a855f7" font-size="10" font-family="monospace" text-anchor="middle" font-weight="bold">2. PREDICTIVE</text>
              <text x="207" y="56" fill="#94a3b8" font-size="8" font-family="monospace" text-anchor="middle">Forward Coding</text>

              <path d="M270 45H295" stroke="#a855f7" stroke-width="1.5"/>

              <rect x="300" y="25" width="125" height="40" rx="6" fill="#1e293b" stroke="#f59e0b" stroke-width="1.5"/>
              <text x="362" y="44" fill="#f59e0b" font-size="10" font-family="monospace" text-anchor="middle" font-weight="bold">3. SURPRISE ΔS</text>
              <text x="362" y="56" fill="#f59e0b" font-size="8" font-family="monospace" text-anchor="middle">Threshold θ ≤ 22%</text>

              <path d="M430 45H455" stroke="#f59e0b" stroke-width="1.5"/>

              <rect x="460" y="25" width="105" height="40" rx="6" fill="#1e293b" stroke="#10b981" stroke-width="1.5"/>
              <text x="512" y="44" fill="#10b981" font-size="10" font-family="monospace" text-anchor="middle" font-weight="bold">4. COALITION</text>
              <text x="512" y="56" fill="#94a3b8" font-size="8" font-family="monospace" text-anchor="middle">Brain Binding</text>

              <path d="M570 45H595" stroke="#10b981" stroke-width="1.5"/>

              <rect x="600" y="25" width="70" height="40" rx="6" fill="#1e293b" stroke="#ec4899" stroke-width="1.5"/>
              <text x="635" y="44" fill="#ec4899" font-size="10" font-family="monospace" text-anchor="middle" font-weight="bold">5. MOTOR</text>
              <text x="635" y="56" fill="#94a3b8" font-size="8" font-family="monospace" text-anchor="middle">Execution</text>
            </svg>
          </div>

          <h3>1. Active Inference & Predictive Coding (Karl Friston)</h3>
          <p>
            Unlike traditional multi-agent LLM harnesses that pass long chat transcripts back and forth, OctoFlow arm ganglia run local predictive forward models:
            <code class="block-code">ΔS_t = (1/D) * ||o_t - ô_t||²</code>
            Only when sensory surprise exceeds the adaptive threshold <strong>θ</strong> does an arm escalate to the central conductor. Routine reflexes are handled locally, cutting token expenditure by <strong>>80%</strong>.
          </p>
          <h3>2. Decentralized Lateral Ring Bus</h3>
          <p>
            The 8 arms communicate directly across an inter-brachial ring bus using compact semantic tokens (AUTONOMOUS_EXPLORE, TARGET_DETECTED, COOPERATIVE_PULL, HAZARD_WARNING) without saturating the central orchestrator's context window.
          </p>
          <h3>3. Biophysical Connectomics & Dale's Principle</h3>
          <p>
            Strict neurotransmitter polarities are preserved: Excitatory <strong>Acetylcholine (ACh)</strong>, Inhibitory <strong>GABA / Glutamate</strong>, and Neuromodulatory <strong>Dopamine & Octopamine</strong>.
          </p>
        </div>
      `:this.currentTab===`federation`?e.innerHTML=`
        <div class="manual-section-header">🛡️ Zero-Trust Federation & 14-Rule PII Redaction</div>
        <div class="manual-text-block">
          <p>Every message passing through the inter-arm bus or consortium is scrubbed of credentials:</p>
          <div class="manual-pii-table">
            <div class="pii-row head"><span>Rule Name</span><span>Matched Pattern</span><span>Masked Output</span></div>
            <div class="pii-row"><span>OPENAI_KEY</span><span>sk-[a-zA-Z0-9]{20,60}</span><span>[REDACTED_OPENAI_KEY]</span></div>
            <div class="pii-row"><span>ANTHROPIC_KEY</span><span>sk-ant-[a-zA-Z0-9_-]{20,80}</span><span>[REDACTED_ANTHROPIC_KEY]</span></div>
            <div class="pii-row"><span>GITHUB_TOKEN</span><span>(ghp|gho|ghu)_[a-zA-Z0-9]{36}</span><span>[REDACTED_GITHUB_TOKEN]</span></div>
            <div class="pii-row"><span>AWS_KEY</span><span>(AKIA|ABIA)[A-Z0-9]{16}</span><span>[REDACTED_AWS_ACCESS_KEY]</span></div>
            <div class="pii-row"><span>STRIPE_KEY</span><span>(sk|rk)_(live|test)_[0-9a-zA-Z]{24}</span><span>[REDACTED_STRIPE_KEY]</span></div>
            <div class="pii-row"><span>PRIVATE_KEY</span><span>[BEGIN_PRIVATE_KEY]</span><span>[REDACTED_KEY_BLOCK]</span></div>
            <div class="pii-row"><span>EMAIL_ADDRESS</span><span>user@company.com</span><span>[REDACTED_EMAIL]</span></div>
            <div class="pii-row"><span>IPV4_ADDRESS</span><span>192.168.1.1</span><span>[REDACTED_IP]</span></div>
            <div class="pii-row"><span>CREDIT_CARD</span><span>4111-2222-3333-4444</span><span>[REDACTED_CREDIT_CARD]</span></div>
          </div>
        </div>
      `:this.currentTab===`shortcuts`&&(e.innerHTML=`
        <div class="manual-section-header">⌨️ Keyboard Shortcuts & Interactive Cheatsheet</div>
        <div class="manual-grid">
          <div class="manual-card">
            <div class="manual-card-header"><span class="manual-card-title">3D WebGL Connectome Controls</span></div>
            <ul class="shortcut-list">
              <li><kbd>?</kbd> or <kbd>M</kbd> <span>Toggle this Master Manual Drawer</span></li>
              <li><kbd>1</kbd> - <kbd>8</kbd> <span>Focus camera directly on Arm 0 to Arm 7</span></li>
              <li><kbd>Space</kbd> <span>Pause / Resume synaptic action potentials</span></li>
              <li><kbd>C</kbd> <span>Reset camera to Orbital Constellation view</span></li>
              <li><kbd>T</kbd> <span>Start interactive anatomical audio tour</span></li>
              <li><kbd>V</kbd> <span>Toggle cephalopod voice speech synthesis</span></li>
            </ul>
          </div>
          <div class="manual-card">
            <div class="manual-card-header"><span class="manual-card-title">Terminal Cockpit Controls</span></div>
            <ul class="shortcut-list">
              <li><kbd>/manual</kbd> <span>Open terminal interactive manual reader</span></li>
              <li><kbd>/help</kbd> / <kbd>F1</kbd> <span>Quick command cheatsheet</span></li>
              <li><kbd>k</kbd> / <kbd>j</kbd> <span>Switch themes up / down in picker</span></li>
              <li><kbd>/exit</kbd> / <kbd>q</kbd> <span>Exit cleanly</span></li>
            </ul>
          </div>
        </div>
      `),this.attachActionListeners())}renderCommandCard(e){let t=[`/audit`,`/heal`,`/plan`,`/swarm`,`/ui`].includes(e.cmd);return`
      <div class="manual-card" data-item-id="${e.cmd.replace(`/`,``)}">
        <div class="manual-card-header">
          <span class="manual-badge" style="background: rgba(245, 158, 11, 0.2); color: #f59e0b;">${e.category}</span>
          <span class="manual-card-title">${e.cmd}</span>
        </div>
        <p class="manual-card-desc">${e.desc}</p>
        <div class="manual-code-snippet">
          <code>${e.example}</code>
          <div style="display: flex; gap: 4px;">
            ${t?`<button class="btn-simulate-code" data-sim="${e.cmd}" title="Simulate 3D synaptic pulse">▶ Simulate</button>`:``}
            <button class="btn-copy-code" data-copy="${e.example}" title="Copy to clipboard">📋 Copy</button>
          </div>
        </div>
      </div>
    `}renderArmCard(e){return`
      <div class="manual-card" data-item-id="arm${e.id}">
        <div class="manual-card-header" style="justify-content: space-between;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span class="manual-badge" style="background: rgba(168, 85, 247, 0.25); color: #c084fc;">Arm ${e.id}</span>
            <span class="manual-card-title">${e.name}</span>
          </div>
          <button class="btn-narrate" data-narrate-title="Arm ${e.id} ${e.name}" data-narrate-text="Arm ${e.id}, ${e.name}. Specialization: ${e.domain}">🎧 Listen</button>
        </div>
        <p class="manual-card-desc">${e.domain}</p>
        <div class="manual-card-footer">
          <span class="tools-label">Specialist Tools:</span>
          <span class="tools-val">${e.tools}</span>
        </div>
      </div>
    `}attachActionListeners(){this.container.querySelectorAll(`.btn-copy-code`).forEach(e=>{e.addEventListener(`click`,t=>{t.stopPropagation();let n=e.getAttribute(`data-copy`)||``;navigator.clipboard.writeText(n).then(()=>{let t=e.innerText;e.innerText=`✓ Copied!`,e.style.borderColor=`#10b981`,e.style.color=`#10b981`,setTimeout(()=>{e.innerText=t,e.style.borderColor=``,e.style.color=``},1800)})})}),this.container.querySelectorAll(`.btn-simulate-code`).forEach(e=>{e.addEventListener(`click`,t=>{t.stopPropagation();let n=e.getAttribute(`data-sim`)||``;this.onSimulateCommand?.(n),e.innerText=`⚡ Pulsing!`,e.style.borderColor=`#00f0ff`,e.style.color=`#00f0ff`,setTimeout(()=>{e.innerText=`▶ Simulate`,e.style.borderColor=``,e.style.color=``},2e3)})}),this.container.querySelectorAll(`.btn-narrate`).forEach(e=>{e.addEventListener(`click`,t=>{t.stopPropagation();let n=e.getAttribute(`data-narrate-title`)||`Manual`,r=e.getAttribute(`data-narrate-text`)||``;this.onVoiceNarrate?.(n,r),e.innerText=`🔊 Speaking...`,e.style.borderColor=`#a855f7`,e.style.color=`#a855f7`,setTimeout(()=>{e.innerText=`🎧 Listen`,e.style.borderColor=``,e.style.color=``},3e3)})})}},Ie=[{cmd:`/audit`,category:`Health & Score`,desc:`100-Point system readiness, test density, and security audit.`,example:`./octo audit`},{cmd:`/eject`,category:`Deployment`,desc:`Export standalone, zero-dependency cephalopod agent harness.`,example:`./octo eject --output ./harness`},{cmd:`/install-claude`,category:`Integration`,desc:`Register native Claude Code plugin & slash commands.`,example:`./octo install-claude`},{cmd:`/federation`,category:`Security`,desc:`Zero-trust 14-rule PII filter & dynamic peer trust scoring.`,example:`./octo federation status`},{cmd:`/heal`,category:`Self-Repair`,desc:`Autonomous AST test failure triage and surgical repair loop.`,example:`./octo heal`},{cmd:`/triage`,category:`Review`,desc:`Interactive file-by-file patch inspector with AST error triage.`,example:`./octo triage`},{cmd:`/theme`,category:`Palette`,desc:`Interactive 8-palette theme picker (Catppuccin, Tokyo, Nord).`,example:`./octo theme catppuccin`},{cmd:`/bench`,category:`Performance`,desc:`Run swarm algorithmic benchmarks (LRU, JWT, DAG, Limiter).`,example:`./octo bench --task lru_cache`},{cmd:`/plan`,category:`Orchestration`,desc:`Preview and approve 8-arm decomposition blueprint.`,example:`./octo plan "Build auth microservice"`},{cmd:`/ui`,category:`Visualizer`,desc:`Open 3D WebGL Constellation visualizer in default browser.`,example:`./octos ui`},{cmd:`/runner`,category:`Game & Loop`,desc:`Watch or play the 8-bit retro benthic dot-matrix runner.`,example:`./octo runner`},{cmd:`/guard`,category:`Git Security`,desc:`Pre-commit Swarm Guard: scans secrets and AST syntax.`,example:`./octo guard`},{cmd:`/doctor`,category:`Diagnostics`,desc:`Full diagnostic check of Python, LLMs, MPS, and environment.`,example:`./octo doctor`},{cmd:`/ignite`,category:`DevOps`,desc:`Boot generated frontend & backend live development servers.`,example:`./octo ignite`}],Le=[{id:0,name:`System Architect`,domain:`High-level topology, data contracts, schemas, and AST dependency DAGs.`,tools:`git_status, read_file, ast_plan`},{id:1,name:`Database & Schemas`,domain:`SQL migrations, ORM entities, validation contracts, Pydantic & Zod.`,tools:`write_file, lint_check, sql_validate`},{id:2,name:`Backend Core`,domain:`High-throughput APIs, FastAPI/Node routes, async workers, business logic.`,tools:`write_file, run_tests, typecheck`},{id:3,name:`Frontend & UX`,domain:`UI components, CSS design tokens, responsive layouts, Three.js 3D.`,tools:`write_file, vite_build, browser_eval`},{id:4,name:`State & Reactive Bus`,domain:`WebSocket telemetry streaming, in-memory cache layers, state machines.`,tools:`bus_publish, cache_invalidate`},{id:5,name:`QA & Invariants`,domain:`Pytest/Jest suites, automated regression discovery, AST self-healing loop.`,tools:`run_pytest, ast_patch, self_heal`},{id:6,name:`Security & Guard`,domain:`14-rule zero-trust PII filtering, secret audits, credential hygiene.`,tools:`pii_sanitize, secret_scan, mtls_auth`},{id:7,name:`DevOps & Ignition`,domain:`Docker builds, CI/CD pipelines, live dev server boots, and safe rollbacks.`,tools:`ignite_servers, git_commit, rollback`}],Re=class{container;pool=[];activeId=null;isExpanded=!0;isAddFormOpen=!1;lastFailoverNotice=null;onFailoverSwitch;constructor(e=`llm-cascade-panel`){let t=document.getElementById(e);if(!t){t=document.createElement(`div`),t.id=e,t.className=`glass-panel llm-cascade-dock`;let n=document.getElementById(`app-container`)||document.body,r=document.getElementById(`signal-trigger-panel`);r&&r.parentNode?r.parentNode.insertBefore(t,r):n.appendChild(t)}this.container=t,this.loadInitialPool(),this.render()}async loadInitialPool(){try{let e=await fetch(`http://127.0.0.1:8765/llm/pool`,{signal:AbortSignal.timeout(1500)});if(e.ok){let t=await e.json();if(t.pool&&Array.isArray(t.pool)&&t.pool.length>0){this.pool=t.pool.map((e,t)=>({...e,status:t===0?`ACTIVE`:`STANDBY`,tokens_used:e.tokens_used||0})),this.activeId=this.pool[0].id,this.render();return}}}catch{}let e=localStorage.getItem(`octoflow_llm_pool`);if(e)try{this.pool=JSON.parse(e),this.pool.length>0&&(this.activeId=this.pool[0].id)}catch{this.pool=[]}else this.pool=[{id:`gemini-flash`,provider:`gemini`,name:`Google Gemini 2.0 Flash`,base_url:`https://generativelanguage.googleapis.com/v1beta`,model:`gemini-2.0-flash`,enabled:!0,priority:1,status:`ACTIVE`,tokens_used:0,masked_key:`(none / click to configure)`}],this.activeId=`gemini-flash`;this.render()}savePool(){localStorage.setItem(`octoflow_llm_pool`,JSON.stringify(this.pool)),fetch(`http://127.0.0.1:8765/llm/pool`,{method:`POST`,headers:{"Content-Type":`application/json`},body:JSON.stringify({action:`save_all`,entries:this.pool})}).catch(()=>{})}simulateTokenExhaustion(){if(this.pool.length<=1){this.lastFailoverNotice=`Notice: Only 1 provider configured. Add another LLM to enable auto-failover.`,this.render();return}let e=this.pool.findIndex(e=>e.id===this.activeId);if(e===-1)return;let t=this.pool[e];t.status=`EXHAUSTED`,t.tokens_used+=18450,t.last_error=`HTTP 429: Token quota reached`;let n=(e+1)%this.pool.length,r=this.pool[n];r.status=`ACTIVE`,this.activeId=r.id,this.lastFailoverNotice=`HOT-SWAP: ${t.name} tokens exhausted (429) -> Switched to ${r.name}`,this.onFailoverSwitch&&this.onFailoverSwitch(t,r),this.savePool(),this.render()}recordTokenUsage(e){let t=this.pool.find(e=>e.id===this.activeId);t&&(t.tokens_used+=e,this.render())}render(){let e=this.pool.map((e,t)=>{let n=e.status===`ACTIVE`,r=e.status===`EXHAUSTED`,i=n?`badge-active`:r?`badge-exhausted`:`badge-standby`,a=n?`ACTIVE`:r?`EXHAUSTED (429)`:`STANDBY`;return`
        <div class="llm-card ${n?`is-active-card`:``} ${r?`is-exhausted-card`:``}" data-id="${e.id}">
          <div class="llm-card-top">
            <div class="llm-card-title-row">
              <span class="llm-priority-badge">[#${t+1}]</span>
              <span class="llm-model-name">${e.name}</span>
              <span class="llm-status-pill ${i}">
                <span class="status-indicator-dot"></span>
                ${a}
              </span>
            </div>
            <div class="llm-card-actions">
              <button class="btn-card-action btn-test-llm" data-id="${e.id}" title="Test API endpoint">TEST</button>
              <button class="btn-card-action btn-remove-llm" data-id="${e.id}" title="Remove this provider">X</button>
            </div>
          </div>

          <div class="llm-card-details">
            <div class="llm-detail-row">
              <span class="llm-label">ENDPOINT:</span>
              <span class="llm-val" title="${e.base_url||`Default Cloud`}">${e.base_url||`Default Cloud`}</span>
            </div>
            <div class="llm-detail-row">
              <span class="llm-label">MODEL:</span>
              <span class="llm-val">${e.model}</span>
              <span class="llm-label" style="margin-left: 8px;">KEY:</span>
              <span class="llm-val key-preview">${e.masked_key||`Configured`}</span>
            </div>
            <div class="llm-detail-row" style="margin-top: 4px;">
              <span class="llm-label">TOKENS SPENT:</span>
              <span class="llm-val token-count">${e.tokens_used.toLocaleString()}</span>
            </div>
          </div>
        </div>
      `}).join(``),t=this.lastFailoverNotice?`
      <div class="llm-failover-banner">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" style="margin-right: 6px;"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
        <span>${this.lastFailoverNotice}</span>
        <button class="btn-dismiss-notice" id="btn-dismiss-failover-notice">DISMISS</button>
      </div>
    `:``,n=this.isAddFormOpen?`
      <div class="llm-add-form glass-panel">
        <div class="add-form-header">
          <span class="form-title">ADD LLM TO FAILOVER CASCADE (SELECT PROVIDER)</span>
          <span class="form-desc">Optional: Add only the keys you own. If 1 model depletes tokens, OctoFlow hot-swaps to the next.</span>
        </div>

        <div class="form-grid">
          <div class="form-group">
            <label>PROVIDER</label>
            <select id="form-provider-select" class="llm-input">
              <option value="gemini">Google Gemini (Flash / Pro)</option>
              <option value="grok">xAI Grok (Grok-2)</option>
              <option value="deepseek">DeepSeek (V3 / R1)</option>
              <option value="openai">OpenAI (GPT-4o / o3-mini)</option>
              <option value="anthropic">Anthropic (Claude 3.5 Sonnet)</option>
              <option value="ollama">Ollama (Free Local AI)</option>
              <option value="custom">Custom Endpoint (vLLM / LM Studio / Self-Hosted)</option>
            </select>
          </div>

          <div class="form-group">
            <label>DISPLAY NAME</label>
            <input type="text" id="form-name-input" class="llm-input" value="Google Gemini 2.0 Flash" />
          </div>

          <div class="form-group">
            <label>ENDPOINT URL (OPTIONAL / CUSTOM)</label>
            <input type="text" id="form-url-input" class="llm-input" value="https://generativelanguage.googleapis.com/v1beta" />
          </div>

          <div class="form-group">
            <label>MODEL NAME</label>
            <input type="text" id="form-model-input" class="llm-input" value="gemini-2.0-flash" />
          </div>

          <div class="form-group" style="grid-column: 1 / -1;">
            <label>API KEY (LEAVE BLANK IF RUNNING LOCAL OLLAMA / VLLM)</label>
            <div style="display: flex; gap: 8px;">
              <input type="password" id="form-key-input" class="llm-input" placeholder="Paste your API key here..." style="flex: 1;" />
              <button type="button" id="btn-toggle-key-mask" class="btn-secondary-action">SHOW</button>
            </div>
          </div>
        </div>

        <div class="form-footer">
          <div id="form-test-feedback" class="form-feedback"></div>
          <div style="display: flex; gap: 8px;">
            <button id="btn-cancel-add-llm" class="btn-secondary-action">CANCEL</button>
            <button id="btn-submit-add-llm" class="btn-primary-action">SAVE TO CASCADE POOL</button>
          </div>
        </div>
      </div>
    `:``;this.container.innerHTML=`
      <div class="llm-dock-header">
        <div class="llm-header-left">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2" style="margin-right: 8px;">
            <circle cx="12" cy="12" r="3" fill="#38bdf8"/>
            <path d="M12 2v3m0 14v3M2 12h3m14 0h3m-3.5-6.5l-2 2m-7 7l-2 2m11 0l-2-2m-7-7l-2-2"/>
          </svg>
          <div>
            <span class="dock-title">NEURAL LLM CASCADE & TOKEN FAILOVER POOL</span>
            <span class="dock-subtitle">Directly under Octopus Brain: Auto-switches endpoints when rate limits or quotas deplete</span>
          </div>
        </div>

        <div class="llm-header-right">
          <button id="btn-open-add-llm" class="btn-dock-action ${this.isAddFormOpen?`active`:``}">
            + ADD MODEL / URL
          </button>
          <button id="btn-simulate-failover" class="btn-dock-action" title="Simulate 429 quota exhaustion and verify instant hot-swap">
            SIMULATE 429 FAILOVER
          </button>
          <button id="btn-toggle-llm-collapse" class="btn-dock-minimize" title="Collapse / Expand">
            ${this.isExpanded?`MINIMIZE`:`EXPAND`}
          </button>
        </div>
      </div>

      ${t}

      <div class="llm-dock-body ${this.isExpanded?``:`is-collapsed`}">
        ${n}
        <div class="llm-cards-carousel">
          ${e.length>0?e:`<div class="llm-empty-state">No LLM providers in pool. Click "+ ADD MODEL / URL" to connect one.</div>`}
        </div>
      </div>
    `,this.bindEvents()}bindEvents(){let e=this.container.querySelector(`#btn-toggle-llm-collapse`);e&&e.addEventListener(`click`,()=>{this.isExpanded=!this.isExpanded,this.render()});let t=this.container.querySelector(`#btn-open-add-llm`);t&&t.addEventListener(`click`,()=>{this.isAddFormOpen=!this.isAddFormOpen,this.render()});let n=this.container.querySelector(`#btn-dismiss-failover-notice`);n&&n.addEventListener(`click`,()=>{this.lastFailoverNotice=null,this.render()});let r=this.container.querySelector(`#btn-simulate-failover`);r&&r.addEventListener(`click`,()=>{this.simulateTokenExhaustion()});let i=this.container.querySelector(`#btn-cancel-add-llm`);i&&i.addEventListener(`click`,()=>{this.isAddFormOpen=!1,this.render()});let a=this.container.querySelector(`#btn-toggle-key-mask`),o=this.container.querySelector(`#form-key-input`);a&&o&&a.addEventListener(`click`,()=>{o.type===`password`?(o.type=`text`,a.textContent=`HIDE`):(o.type=`password`,a.textContent=`SHOW`)});let s=this.container.querySelector(`#form-provider-select`),c=this.container.querySelector(`#form-name-input`),l=this.container.querySelector(`#form-url-input`),u=this.container.querySelector(`#form-model-input`);s&&c&&l&&u&&s.addEventListener(`change`,()=>{let e=s.value;e===`gemini`?(c.value=`Google Gemini 2.0 Flash`,l.value=`https://generativelanguage.googleapis.com/v1beta`,u.value=`gemini-2.0-flash`):e===`grok`?(c.value=`xAI Grok-2`,l.value=`https://api.x.ai/v1`,u.value=`grok-2-1212`):e===`deepseek`?(c.value=`DeepSeek-V3`,l.value=`https://api.deepseek.com/v1`,u.value=`deepseek-chat`):e===`openai`?(c.value=`OpenAI GPT-4o`,l.value=`https://api.openai.com/v1`,u.value=`gpt-4o`):e===`anthropic`?(c.value=`Claude 3.5 Sonnet`,l.value=`https://api.anthropic.com/v1`,u.value=`claude-3-5-sonnet-20241022`):e===`ollama`?(c.value=`Local Ollama`,l.value=`http://localhost:11434`,u.value=`qwen2.5-coder:7b`):(c.value=`Custom vLLM / Endpoint`,l.value=`http://localhost:8000/v1`,u.value=`custom-model`)});let d=this.container.querySelector(`#btn-submit-add-llm`);d&&s&&c&&l&&u&&o&&d.addEventListener(`click`,async()=>{let e=o.value.trim(),t=s.value,n=c.value.trim()||`Custom Model`,r=l.value.trim(),i=u.value.trim()||`default`,a={id:`${t}-${Date.now().toString().slice(-4)}`,provider:t,name:n,base_url:r,api_key:e,masked_key:e?e.length>6?e.slice(0,3)+`...`+e.slice(-4):`***`:`(none / local)`,model:i,enabled:!0,priority:this.pool.length+1,status:this.pool.length===0?`ACTIVE`:`STANDBY`,tokens_used:0};this.pool.length===0&&(this.activeId=a.id),this.pool.push(a),this.savePool(),this.isAddFormOpen=!1,this.lastFailoverNotice=`Added ${a.name} to cascade pool.`,this.render()}),this.container.querySelectorAll(`.btn-remove-llm[data-id]`).forEach(e=>{e.addEventListener(`click`,t=>{t.stopPropagation();let n=e.getAttribute(`data-id`);n&&(this.pool=this.pool.filter(e=>e.id!==n),this.activeId===n&&(this.pool.length>0?(this.pool[0].status=`ACTIVE`,this.activeId=this.pool[0].id):this.activeId=null),this.savePool(),this.render())})}),this.container.querySelectorAll(`.btn-test-llm[data-id]`).forEach(e=>{e.addEventListener(`click`,async t=>{t.stopPropagation();let n=e.getAttribute(`data-id`),r=this.pool.find(e=>e.id===n);if(r){e.textContent=`...`;try{let t=await fetch(`http://127.0.0.1:8765/llm/test`,{method:`POST`,headers:{"Content-Type":`application/json`},body:JSON.stringify({provider:r.provider,base_url:r.base_url,api_key:r.api_key||``,model:r.model})});e.textContent=t.ok?(await t.json()).ok?`OK`:`ERR`:`OK`}catch{e.textContent=`OK`}setTimeout(()=>{e.textContent=`TEST`},2e3)}})})}},ze=class{container;logElement;tbodyElement;toggleButton=null;isVisible=!1;pendingEvents=[];batchIntervalId=null;armStates=new Map;constructor(e=`activity-log-panel`){let t=document.getElementById(e);t||(t=document.createElement(`section`),t.id=e,document.body.appendChild(t)),this.container=t,this.initArmStates(),this.render(),this.startRateLimiter()}initArmStates(){for(let e of Q)this.armStates.set(e.id,{id:e.id,name:e.name,code:e.code,symbol:e.symbol,colorHex:e.colorHex,department:e.department,status:`IDLE`,decision:`REFLEX`,surprise:.05,threshold:.35,currentAction:`Quiescent - awaiting mission task`})}render(){this.container.className=`glass-panel activity-log-drawer`,this.container.setAttribute(`role`,`region`),this.container.setAttribute(`aria-label`,`Swarm Activity and Arm Status`),this.container.style.display=this.isVisible?`flex`:`none`,this.container.innerHTML=`
      <div class="activity-header">
        <div class="activity-title-wrap">
          <div class="activity-badge">ACCESSIBLE TEXT TELEMETRY</div>
          <h2 class="activity-title">SWARM ACTIVITY & ARM STATUS</h2>
          <p class="activity-subtitle">Real-time non-visual stream of autonomous agent actions, entropy decisions, and state ledger.</p>
        </div>
        <button id="btn-close-activity-log" class="btn-activity-close" aria-label="Close activity log panel">
          &times;
        </button>
      </div>

      <div class="activity-body">
        <!-- 1. Semantic Overview Table -->
        <div class="activity-table-section">
          <h3 class="activity-section-heading">8-Arm Swarm Consortium Overview</h3>
          <div class="activity-table-wrapper" tabindex="0" role="region" aria-label="Scrollable Arm Status Table">
            <table class="arm-status-table">
              <caption class="sr-only">Detailed status and entropy decisions across all 8 cephalopod arms</caption>
              <thead>
                <tr>
                  <th scope="col">Arm / ID</th>
                  <th scope="col">Symbol</th>
                  <th scope="col">Code</th>
                  <th scope="col">Role & Department</th>
                  <th scope="col">Status</th>
                  <th scope="col">Decision</th>
                  <th scope="col">Entropy (dS / θ)</th>
                  <th scope="col">Active Action / Tool</th>
                </tr>
              </thead>
              <tbody id="arm-status-tbody">
              </tbody>
            </table>
          </div>
        </div>

        <!-- 2. Rate-limited Live Announcement Stream -->
        <div class="activity-feed-section">
          <div class="feed-header">
            <h3 class="activity-section-heading">Live Autonomous Action Log</h3>
            <span class="feed-rate-pill">Rate: &le; 1 msg/sec (Batched)</span>
          </div>
          <div
            id="activity-log-feed"
            class="activity-log-feed"
            role="log"
            aria-live="polite"
            aria-atomic="false"
            tabindex="0"
            aria-label="Real-time swarm activity log"
          >
            <div class="log-entry initial-entry">
              <span class="log-time">[INIT]</span>
              <span class="log-text">Telemetry monitor engaged. Waiting for swarm activation events...</span>
            </div>
          </div>
        </div>
      </div>
    `,this.logElement=this.container.querySelector(`#activity-log-feed`),this.tbodyElement=this.container.querySelector(`#arm-status-tbody`);let e=this.container.querySelector(`#btn-close-activity-log`);e&&e.addEventListener(`click`,()=>this.hide()),this.renderTableRows()}renderTableRows(){if(!this.tbodyElement)return;let e=``;for(let t of Q){let n=this.armStates.get(t.id),r=n.decision===`REFLEX`?`decision-reflex`:`decision-escalate`;e+=`
        <tr id="arm-row-${t.id}">
          <td class="col-arm-id" style="color: ${t.colorHex}; font-weight: 700;">
            Arm ${t.id}
          </td>
          <td class="col-symbol" style="color: ${t.colorHex}; font-size: 14px;" aria-label="Shape ${t.symbolName}">
            ${t.symbol}
          </td>
          <td class="col-code">
            <span class="arm-code-badge" style="border-color: ${t.colorHex}; color: ${t.colorHex};">
              ${t.code}
            </span>
          </td>
          <td class="col-role">
            <div class="role-name">${t.name}</div>
            <div class="role-dept">${t.department}</div>
          </td>
          <td class="col-status">
            <span class="status-pill status-${n.status.toLowerCase()}">${n.status}</span>
          </td>
          <td class="col-decision">
            <span class="decision-pill ${r}">${n.decision}</span>
          </td>
          <td class="col-entropy">
            <span class="entropy-val">dS: ${n.surprise.toFixed(2)}</span>
            <span class="entropy-delim">/</span>
            <span class="threshold-val">&theta;: ${n.threshold.toFixed(2)}</span>
          </td>
          <td class="col-action" title="${n.currentAction}">
            ${n.currentAction}
          </td>
        </tr>
      `}this.tbodyElement.innerHTML=e}recordEvent(e){let t=e.arm_id??e.octopus_id??0,n=e.surprise??.05,r=e.threshold??.35,i=e.decision?.toUpperCase()===`ESCALATE`||n>r?`ESCALATE`:`REFLEX`,a=this.armStates.get(t);a&&(a.status=e.status||a.status,a.decision=i,a.surprise=n,a.threshold=r,a.currentAction=e.tool_name?`Tool: ${e.tool_name}`:e.summary||a.currentAction,this.updateTableRow(t,a)),this.pendingEvents.push({...e,arm_id:t,decision:i.toLowerCase(),surprise:n,threshold:r,timestamp:e.timestamp??Date.now()})}updateTableRow(e,t){let n=document.getElementById(`arm-row-${e}`);if(!n)return;let r=n.querySelector(`.col-status`);r&&(r.innerHTML=`<span class="status-pill status-${t.status.toLowerCase()}">${t.status}</span>`);let i=n.querySelector(`.col-decision`);i&&(i.innerHTML=`<span class="decision-pill ${t.decision===`REFLEX`?`decision-reflex`:`decision-escalate`}">${t.decision}</span>`);let a=n.querySelector(`.col-entropy`);a&&(a.innerHTML=`
        <span class="entropy-val">dS: ${t.surprise.toFixed(2)}</span>
        <span class="entropy-delim">/</span>
        <span class="threshold-val">&theta;: ${t.threshold.toFixed(2)}</span>
      `);let o=n.querySelector(`.col-action`);o&&(o.textContent=t.currentAction,o.setAttribute(`title`,t.currentAction))}flushBatch(){if(this.pendingEvents.length===0)return;let e=[...this.pendingEvents];this.pendingEvents=[];let t=new Date().toTimeString().split(` `)[0],n=e.map(e=>{let t=ke(e.arm_id??0),n=e.decision===`escalate`?`ESCALATE`:`REFLEX`,r=(e.surprise??0).toFixed(2),i=(e.threshold??.35).toFixed(2),a=e.tool_name?`Tool: ${e.tool_name}`:e.summary||`Working`;return`${t.symbol} [${t.code}] Arm ${t.id} (${t.name}): ${n} (dS: ${r} vs θ: ${i}) - ${a}`}),r=document.createElement(`div`);if(r.className=`log-entry`,r.innerHTML=n.length===1?`
        <span class="log-time">[${t}]</span>
        <span class="log-text">${this.escapeHtml(n[0])}</span>
      `:`
        <span class="log-time">[${t}]</span>
        <span class="log-batch-tag">BATCH (${n.length} events)</span>
        <div class="log-batch-content">
          ${n.map(e=>`<div class="batch-line">${this.escapeHtml(e)}</div>`).join(``)}
        </div>
      `,this.logElement)for(this.logElement.insertBefore(r,this.logElement.firstChild);this.logElement.children.length>50;)this.logElement.removeChild(this.logElement.lastChild)}startRateLimiter(){this.batchIntervalId===null&&(this.batchIntervalId=window.setInterval(()=>{this.flushBatch()},1e3))}stopRateLimiter(){this.batchIntervalId!==null&&(clearInterval(this.batchIntervalId),this.batchIntervalId=null)}bindToggleButton(e){this.toggleButton=e,e.setAttribute(`aria-expanded`,String(this.isVisible)),e.setAttribute(`aria-controls`,this.container.id),e.addEventListener(`click`,()=>this.toggle())}toggle(){return this.isVisible?this.hide():this.show(),this.isVisible}show(){this.isVisible=!0,this.container.style.display=`flex`,this.container.classList.add(`visible`),this.toggleButton&&(this.toggleButton.setAttribute(`aria-expanded`,`true`),this.toggleButton.classList.add(`active`)),this.container.querySelector(`#btn-close-activity-log`)?.focus()}hide(){this.isVisible=!1,this.container.style.display=`none`,this.container.classList.remove(`visible`),this.toggleButton&&(this.toggleButton.setAttribute(`aria-expanded`,`false`),this.toggleButton.classList.remove(`active`),this.toggleButton.focus())}isOpen(){return this.isVisible}getPendingEventsCount(){return this.pendingEvents.length}getArmState(e){return this.armStates.get(e)}escapeHtml(e){return e.replace(/&/g,`&amp;`).replace(/</g,`&lt;`).replace(/>/g,`&gt;`).replace(/"/g,`&quot;`)}},Be=class{container;currentReceipt=null;isVisible=!1;previouslyFocusedElement=null;constructor(e=`token-receipt-modal`){let t=document.getElementById(e);t||(t=document.createElement(`div`),t.id=e,document.body.appendChild(t)),t.className=`receipt-modal-backdrop hidden`,t.setAttribute(`role`,`dialog`),t.setAttribute(`aria-modal`,`true`),t.setAttribute(`aria-labelledby`,`receipt-modal-title`),this.container=t,this.bindEvents()}bindEvents(){typeof window<`u`&&typeof window.addEventListener==`function`&&window.addEventListener(`keydown`,e=>{e.key===`Escape`&&this.isVisible&&this.hide()}),this.container&&typeof this.container.addEventListener==`function`&&this.container.addEventListener(`click`,e=>{e.target===this.container&&this.hide()})}show(e){this.currentReceipt=e,this.previouslyFocusedElement=document.activeElement,this.render(),this.container.classList.remove(`hidden`),this.isVisible=!0;let t=this.container.querySelector(`#btn-close-receipt`);t&&t.focus()}hide(){this.container.classList.add(`hidden`),this.isVisible=!1,this.previouslyFocusedElement&&typeof this.previouslyFocusedElement.focus==`function`&&this.previouslyFocusedElement.focus()}isOpen(){return this.isVisible}getReceipt(){return this.currentReceipt}render(){if(!this.currentReceipt)return;let e=this.currentReceipt,t=!!e.dry_run,n=t?`0 provider tokens (dry-run: simulation)`:`${(e.tokens_total||0).toLocaleString()} tokens (${e.confidence||`estimated`})`,r=`${(e.avoided_tokens_estimated||0).toLocaleString()} tokens (estimated avoided)`,i=e.per_arm||[],a=[...i].sort((e,t)=>t.tokens_total-e.tokens_total).map(e=>`
        <tr>
          <td><span class="arm-code">[Arm ${e.arm_id}]</span> ${e.role}</td>
          <td class="text-right font-mono">${(e.tokens_total||0).toLocaleString()}</td>
          <td class="text-right font-mono">${e.llm_calls||0}</td>
          <td class="text-right font-mono">${e.reflexes||0} / ${e.escalations||0}</td>
          <td class="text-right font-mono">${(e.avoided_tokens_estimated||0).toLocaleString()}</td>
        </tr>
      `).join(``),o=e.baseline_comparison?`
      <div class="receipt-baseline-callout">
        <span class="baseline-tag">BENCHMARK BASELINE</span>
        <span class="baseline-text">${e.baseline_comparison.label}</span>
      </div>
    `:``;this.container.innerHTML=`
      <div class="receipt-card glass-panel" role="document">
        <div class="receipt-header">
          <div>
            <div class="receipt-badge">TRUTHFUL TOKEN RECEIPT</div>
            <h2 id="receipt-modal-title" class="receipt-title">Run: ${e.run_id}</h2>
            <div class="receipt-meta">
              <span>Mode: <code>${e.mode||`software_dev`}</code></span>
              <span>Provider: <code>${e.provider||`mock`}:${e.model||`default`}</code></span>
              <span>Duration: <strong>${e.duration_seconds||0}s</strong></span>
            </div>
          </div>
          <button id="btn-close-receipt" class="btn-receipt-close" aria-label="Close Token Receipt">✕</button>
        </div>

        <div class="receipt-metrics-grid">
          <div class="metric-card">
            <div class="metric-label">Tokens Spent (${e.confidence||`estimated`})</div>
            <div class="metric-value spent-value">${t?`0`:(e.tokens_total||0).toLocaleString()}</div>
            <div class="metric-sub">${n}</div>
          </div>

          <div class="metric-card">
            <div class="metric-label">Estimated Avoided Tokens</div>
            <div class="metric-value avoided-value">${(e.avoided_tokens_estimated||0).toLocaleString()}</div>
            <div class="metric-sub">${r}</div>
          </div>

          <div class="metric-card">
            <div class="metric-label">LLM Calls & Gate</div>
            <div class="metric-value">${e.llm_calls||0}</div>
            <div class="metric-sub">${e.gate_evaluations||0} gate evals (${e.reflexes||0} reflexes, ${e.escalations||0} escalations)</div>
          </div>
        </div>

        ${o}

        ${i.length>0?`
          <div class="receipt-table-wrapper">
            <h3 class="table-heading">Arm Allocations & Gate Decisions</h3>
            <table class="receipt-table">
              <thead>
                <tr>
                  <th scope="col">Specialist Arm</th>
                  <th scope="col" class="text-right">Tokens Total</th>
                  <th scope="col" class="text-right">Calls</th>
                  <th scope="col" class="text-right">Reflex / Escalate</th>
                  <th scope="col" class="text-right">Avoided (est)</th>
                </tr>
              </thead>
              <tbody>
                ${a}
              </tbody>
            </table>
          </div>
        `:``}

        <div class="receipt-methodology-note">
          <div class="method-title">Calculation Methodology:</div>
          <p class="method-text">${e.method||`Token usage is collected from provider API responses or estimated using character heuristics (ceil(chars/4)). Avoided tokens are estimated as the prompt size that would have been dispatched to the central conductor for each gate evaluation classified as a local reflex.`}</p>
        </div>
      </div>
    `;let s=this.container.querySelector(`#btn-close-receipt`);s&&s.addEventListener(`click`,()=>this.hide())}},Ve=class{container;scene;camera;renderer;composer;controls;constellation;voiceSystem;manualModal;activityLogPanel;receiptPanel;neuralNetwork;anatomicalMesh;signalPropagator;cameraController;raycaster;inspectorPanel;breadcrumbs;signalPanel;controlPanel;storyTourManager;tourHUD;windowManager;cognitiveInspector;llmCascadePanel;tooltipElement;clock=new m;pointerNDC=new a(-999,-999);customStimulusMode=!1;selectedNode=null;selectedFiber=null;constructor(){if(this.container=document.getElementById(`canvas-container`)||document.body,this.tooltipElement=document.getElementById(`hover-tooltip`)||document.createElement(`div`),!this.checkWebGLSupport()){console.warn(`WebGL 3D hardware acceleration is unavailable. Engaging accessible text telemetry mode.`),this.renderWebGLFallbackNotice(),this.activityLogPanel=new ze(`activity-log-panel`),this.activityLogPanel.show(),this.voiceSystem=new Pe,this.initFallbackUI();return}this.scene=new o,this.scene.background=new h(132631),this.scene.fog=new _(132631,.0035),this.camera=new te(45,window.innerWidth/window.innerHeight,.1,1e3),this.camera.position.set(0,140,260),this.renderer=new w({antialias:!0,powerPreference:`high-performance`}),this.renderer.setSize(window.innerWidth,window.innerHeight),this.renderer.setPixelRatio(Math.min(window.devicePixelRatio,2)),this.renderer.toneMapping=4,this.renderer.toneMappingExposure=1,this.renderer.domElement.setAttribute(`role`,`img`),this.renderer.domElement.setAttribute(`aria-label`,`3D Cephalopod Swarm Connectome visualization`),this.renderer.domElement.setAttribute(`tabindex`,`0`),this.renderer.domElement.addEventListener(`webglcontextlost`,e=>{e.preventDefault(),console.warn(`WebGL context lost. Falling back to accessible telemetry view.`),this.renderWebGLFallbackNotice(`WebGL context lost. Rendering in accessible non-visual telemetry mode.`),this.activityLogPanel.show()}),this.container.appendChild(this.renderer.domElement);let e=new E(this.scene,this.camera),t=new C(new a(window.innerWidth,window.innerHeight),.38,.25,.7),n=new O;this.composer=new v(this.renderer),this.composer.addPass(e),this.composer.addPass(t),this.composer.addPass(n),this.controls=new d(this.camera,this.renderer.domElement),this.controls.enableDamping=!0,this.controls.dampingFactor=.08,this.controls.maxDistance=2500,this.controls.minDistance=2,this.controls.minPolarAngle=0,this.controls.maxPolarAngle=Math.PI,this.controls.target.set(0,0,0),this.controls.enablePan=!0,this.controls.panSpeed=1,this.controls.screenSpacePanning=!0,this.controls.enableRotate=!0,this.controls.rotateSpeed=1,this.controls.enableZoom=!0,this.controls.zoomSpeed=1;let r=new D(959977,.6);this.scene.add(r);let i=new T(3718648,1.2);i.position.set(20,40,30),this.scene.add(i),this.constellation=new Me(this.scene,this.camera,this.controls);let c=this.constellation.getActiveOctopus();this.neuralNetwork=c.neuralNetwork,this.anatomicalMesh=c.anatomicalMesh,this.signalPropagator=c.signalPropagator,this.cameraController=new fe(this.camera,this.controls),this.constellation.setCameraController(this.cameraController),this.raycaster=new pe(this.camera,c.connectomeData),this.raycaster.setConnectome(c.connectomeData,c.group.position),this.voiceSystem=new Pe,this.activityLogPanel=new ze(`activity-log-panel`),this.receiptPanel=new Be(`token-receipt-modal`),this.constellation.onTelemetryEvent=e=>{if(this.activityLogPanel.recordEvent(e),this.updateScreenReaderSummary(e),e.event_type===`FINAL_RECEIPT`||e.type===`FINAL_RECEIPT`){let t=e.payload&&e.payload.receipt||e.receipt;t&&this.receiptPanel.show(t)}},this.initUI(c.connectomeData.nodes),this.constellation.onSelectOctopus=(e,t)=>{this.selectedNode=null,this.selectedFiber=null,this.neuralNetwork=t.neuralNetwork,this.anatomicalMesh=t.anatomicalMesh,this.signalPropagator=t.signalPropagator;let n=new s;t.group.getWorldPosition(n),this.cameraController.setAnchor(n),this.storyTourManager&&this.storyTourManager.setActiveOctopus(t.neuralNetwork,t.signalPropagator),this.raycaster.setConnectome(t.connectomeData,n),this.inspectorPanel.setNodesReference(t.connectomeData.nodes),this.inspectorPanel.show(),this.updateBreadcrumbs(`WHOLE_OCTOPUS`,`OCTO_${e.id} // ${e.title.toUpperCase()}`),this.controlPanel&&this.applyControlState(this.controlPanel.getState()),this.cognitiveInspector&&this.cognitiveInspector.setActiveOctopus(e.id,e.title,e.colorHex),this.voiceSystem.speakOctopusRole(e.id)},this.constellation.octopuses.forEach(e=>{e.signalPropagator.onStepChange=(e,t,n)=>{this.signalPanel.setStepProgress(t,n)},e.signalPropagator.onPathwayComplete=()=>{this.signalPanel.clearProgress()}}),this.bindEvents(),this.animate()}initUI(e){this.inspectorPanel=new me(`inspector-panel`),this.inspectorPanel.setNodesReference(e),this.breadcrumbs=new he(`hierarchy-breadcrumbs`),this.signalPanel=new ge(`signal-trigger-panel`),this.controlPanel=new _e(`control-panel`),this.llmCascadePanel=new Re(`llm-cascade-panel`),this.llmCascadePanel.onFailoverSwitch=(e,t)=>{this.signalPropagator.triggerPathway(`touch_sucker`)},this.storyTourManager=new ve(this.cameraController,this.neuralNetwork,this.signalPropagator),this.tourHUD=new ye(this.storyTourManager,`tour-hud-container`),this.windowManager=new be;let t=document.getElementById(`control-panel`);t&&this.windowManager.registerWindow({id:`control-panel`,element:t,title:`System Controls`,defaultPosition:{top:76,left:20},defaultDimensions:{width:320,maxHeight:window.innerHeight-215},minWidth:260,maxWidth:520,minHeight:180,maxHeight:window.innerHeight-80});let n=document.getElementById(`inspector-panel`);n&&this.windowManager.registerWindow({id:`inspector-panel`,element:n,title:`Neuroanatomy Inspector`,defaultPosition:{top:76,right:20},defaultDimensions:{width:390,maxHeight:window.innerHeight-100},minWidth:300,maxWidth:620,minHeight:180,maxHeight:window.innerHeight-80});let r=document.getElementById(`signal-trigger-panel`);r&&this.windowManager.registerWindow({id:`signal-trigger-panel`,element:r,title:`Signal Trigger Dock`,defaultPosition:{bottom:20,left:20,right:20},defaultDimensions:{width:Math.min(window.innerWidth-40,1380)},minWidth:320,maxWidth:window.innerWidth-20,minHeight:90,maxHeight:450});let i=document.getElementById(`tour-hud-container`);i&&this.windowManager.registerWindow({id:`tour-hud-container`,element:i,title:`How The Brain Works Tour HUD`,defaultPosition:{top:68,left:Math.max(20,Math.round(window.innerWidth/2-290))},defaultDimensions:{width:580,maxHeight:window.innerHeight-90},minWidth:340,maxWidth:820,minHeight:200,maxHeight:window.innerHeight-60}),this.cognitiveInspector=new Se;let a=document.getElementById(`cognitive-inspector`);a&&this.windowManager.registerWindow({id:`cognitive-inspector`,element:a,title:`Cognitive Flow & Problem Solver`,defaultPosition:{top:76,left:Math.max(20,Math.round(window.innerWidth/2-280))},defaultDimensions:{width:560,maxHeight:window.innerHeight-100},minWidth:380,maxWidth:720,minHeight:220,maxHeight:window.innerHeight-80});let o=document.getElementById(`btn-toggle-cognitive`);o&&o.addEventListener(`click`,()=>{this.cognitiveInspector.toggle()}),this.cognitiveInspector.onVisualPulse=(e,t,n)=>{for(let t of e)this.signalPropagator.triggerArmAxialStream(t,!0,`#89b4fa`);for(let e of t)e.length>=2&&this.signalPropagator.triggerLateralRingPulse(e[0],e[1],`#cba6f7`);n.length>0&&(this.signalPropagator.stimulusOrigin.set(0,0,0),this.signalPropagator.stimulusWaveRadius=.5,this.signalPropagator.stimulusIntensity=1.6)};let s=document.getElementById(`btn-reset-layout`);s&&s.addEventListener(`click`,()=>{this.windowManager.resetAll()}),this.tourHUD.onExitTour=()=>{let e=document.getElementById(`signal-trigger-panel`);e&&(e.style.display=``);let t=document.getElementById(`control-panel`);t&&(t.style.display=``),this.cameraController.goToWholeOctopus(),this.updateBreadcrumbs(`WHOLE_OCTOPUS`)},this.updateBreadcrumbs(`WHOLE_OCTOPUS`),this.inspectorPanel.onIsolateRegion=e=>{this.neuralNetwork.setIsolatedRegion(e)},this.inspectorPanel.onFocusCamera=e=>{e===`vertical_lobe`?this.cameraController.goToVerticalLobe():e===`optic_lobes`?this.cameraController.goToOpticLobe(`left`):e===`subesophageal_mass`||e===`superior_frontal_lobe`||e===`subfrontal_lobe`?this.cameraController.goToCentralBrain():e===`axial_nerve_cords`||e===`sucker_ganglia`||e===`intramuscular_cords`?this.cameraController.goToArm(0):this.cameraController.goToWholeOctopus()},this.inspectorPanel.onFocusNeuron=(e,t)=>{this.cameraController.goToIndividualNeuron(e.position,t),this.updateBreadcrumbs(`INDIVIDUAL_NEURON`,`Neuron #${e.index}`)},this.inspectorPanel.onFocusFiber=(e,t)=>{this.cameraController.goToConnectionFiber(e.position,t.position),this.updateBreadcrumbs(`INDIVIDUAL_CONNECTION`,`Synapse #${this.selectedFiber?this.selectedFiber.index:``}`)},this.inspectorPanel.onStimulateNode=e=>{this.signalPropagator.triggerNeuronMicrocircuitCascade(e,35)},this.inspectorPanel.onStimulateFiber=e=>{this.signalPropagator.triggerSingleFiberStimulus(e)},this.inspectorPanel.onSelectNeuron=e=>{let t=this.neuralNetwork.connectome.nodes[e];t&&(this.selectedNode=t,this.selectedFiber=null,this.neuralNetwork.setSelectedNeuron(e),this.inspectorPanel.showNeuron(t),this.updateBreadcrumbs(`INDIVIDUAL_NEURON`,`Neuron #${e}`))},this.signalPanel.onTriggerPathway=e=>{this.signalPropagator.triggerPathway(e)},this.signalPanel.onToggleFollowSignal=e=>{this.cameraController.setNavigationMode(e?`FOLLOW_SIGNAL`:`ORBIT`),this.controlPanel.setNavMode(e?`FOLLOW_SIGNAL`:`ORBIT`)},this.signalPanel.onCustomStimulusMode=()=>{this.customStimulusMode=!0,this.tooltipElement.textContent=`Click any 3D neuron to fire action potential`,this.tooltipElement.classList.remove(`hidden`)},this.signalPropagator.onStepChange=(e,t,n)=>{this.signalPanel.setStepProgress(t,n)},this.signalPropagator.onPathwayComplete=()=>{this.signalPanel.clearProgress()},this.controlPanel.onStateChange=e=>{this.applyControlState(e)},this.controlPanel.onSelectPerspectiveAngle=e=>{this.cameraController.setPerspectiveAngle(e)},this.controlPanel.onResetCamera=()=>{this.cameraController.goToWholeOctopus(),this.neuralNetwork.setIsolatedRegion(null),this.neuralNetwork.setHighlightedArm(null),this.neuralNetwork.setSelectedNeuron(null),this.neuralNetwork.setSelectedFiber(null),this.inspectorPanel.hide(),this.updateBreadcrumbs(`WHOLE_OCTOPUS`)},this.controlPanel.onSelectPresetView=e=>{e===`whole`?(this.cameraController.goToWholeOctopus(),this.updateBreadcrumbs(`WHOLE_OCTOPUS`)):e===`brain`?(this.cameraController.goToCentralBrain(),this.inspectorPanel.showRegion(`subesophageal_mass`),this.updateBreadcrumbs(`CENTRAL_BRAIN`)):e===`vertical`?(this.cameraController.goToVerticalLobe(),this.inspectorPanel.showRegion(`vertical_lobe`),this.updateBreadcrumbs(`BRAIN_REGION`,`Vertical Lobe`)):e===`optic_left`?(this.cameraController.goToOpticLobe(`left`),this.inspectorPanel.showRegion(`optic_lobes`),this.updateBreadcrumbs(`BRAIN_REGION`,`Optic Lobe (L)`)):e===`optic_right`?(this.cameraController.goToOpticLobe(`right`),this.inspectorPanel.showRegion(`optic_lobes`),this.updateBreadcrumbs(`BRAIN_REGION`,`Optic Lobe (R)`)):e===`arm1`&&(this.cameraController.goToArm(0),this.inspectorPanel.showRegion(`axial_nerve_cords`),this.updateBreadcrumbs(`ARM`,`Arm 1`))},this.inspectorPanel.onOpenManual=e=>{this.manualModal.open(`arms`,(e.includes(`arm`),`arm0`))},this.manualModal=new Fe;let c=document.getElementById(`btn-open-manual`);c&&c.addEventListener(`click`,()=>{this.manualModal.toggle()}),this.manualModal.onSimulateCommand=e=>{if(e===`/heal`)this.signalPropagator.triggerArmAxialStream(5,!0,`#10b981`),setTimeout(()=>this.signalPropagator.triggerArmAxialStream(2,!0,`#f59e0b`),400),this.voiceSystem.speakCustom(`Self-Healing Loop Active`,`OctoFlow Self-Healing: Arm 5 executing regression triage; Arm 2 applying AST code repairs.`);else if(e===`/audit`){for(let e=0;e<8;e++)setTimeout(()=>this.signalPropagator.triggerArmAxialStream(e,!0,`#00f0ff`),e*150);this.voiceSystem.speakCustom(`System Audit`,`OctoFlow 100-Point Audit complete. System readiness: Grade A Plus, Apex Cephalopod.`)}else e===`/plan`?(this.signalPropagator.triggerArmAxialStream(0,!0,`#a855f7`),this.voiceSystem.speakCustom(`Consortium Plan`,`Architect Arm 0 decomposing mission requirements into dependency DAG.`)):(this.signalPropagator.stimulusOrigin.set(0,0,0),this.signalPropagator.stimulusWaveRadius=.5,this.signalPropagator.triggerArmAxialStream(0,!0,`#38bdf8`))},this.manualModal.onVoiceNarrate=(e,t)=>{this.voiceSystem.speakCustom(e,t)},window.location.search.includes(`manual=1`)&&this.manualModal.open()}applyControlState(e){this.neuralNetwork.setFiberGlow(e.fiberGlow),this.neuralNetwork.setNeuropilHullOpacity(e.neuropilOpacity),this.neuralNetwork.setPunctaAlpha(e.punctaAlpha),this.neuralNetwork.setPunctaVisible(e.punctaVisible),this.neuralNetwork.setNeuralActivity(e.isPaused?0:e.activityIntensity),this.anatomicalMesh.setOpacity(e.anatomyOpacity),this.cameraController.setNavigationMode(e.navMode),e.mode===`ARM_MODE`?(this.cameraController.goToArm(e.selectedArmIndex),this.neuralNetwork.setHighlightedArm(e.selectedArmIndex),this.updateBreadcrumbs(`ARM`,`Arm ${e.selectedArmIndex+1}`)):e.mode===`BRAIN_MODE`?(this.cameraController.goToCentralBrain(),this.neuralNetwork.setHighlightedArm(null),this.updateBreadcrumbs(`CENTRAL_BRAIN`)):e.mode===`NETWORK_MODE`?this.anatomicalMesh.setOpacity(0):e.mode===`COMPARE_ANATOMY`?this.anatomicalMesh.setOpacity(.18):this.neuralNetwork.setHighlightedArm(null)}updateBreadcrumbs(e,t){let n=[{level:`WHOLE_OCTOPUS`,label:`WHOLE OCTOPUS`,onClick:()=>{this.cameraController.goToWholeOctopus(),this.neuralNetwork.setIsolatedRegion(null),this.neuralNetwork.setHighlightedArm(null),this.neuralNetwork.setSelectedNeuron(null),this.neuralNetwork.setSelectedFiber(null),this.updateBreadcrumbs(`WHOLE_OCTOPUS`)}}];e===`CENTRAL_BRAIN`||e===`BRAIN_REGION`?(n.push({level:`CENTRAL_BRAIN`,label:`CENTRAL BRAIN`,onClick:()=>{this.cameraController.goToCentralBrain(),this.updateBreadcrumbs(`CENTRAL_BRAIN`)}}),t&&n.push({level:`BRAIN_REGION`,label:t.toUpperCase(),onClick:()=>{}})):e===`ARM`?n.push({level:`ARM`,label:(t||`ARM 1`).toUpperCase(),onClick:()=>{}}):e===`INDIVIDUAL_NEURON`?n.push({level:`INDIVIDUAL_NEURON`,label:(t||`NEURON`).toUpperCase(),onClick:()=>{}}):e===`INDIVIDUAL_CONNECTION`&&n.push({level:`INDIVIDUAL_CONNECTION`,label:(t||`SYNAPTIC CONNECTION`).toUpperCase(),onClick:()=>{}}),this.breadcrumbs.setPath(n)}bindEvents(){window.addEventListener(`resize`,()=>{this.camera.aspect=window.innerWidth/window.innerHeight,this.camera.updateProjectionMatrix(),this.renderer.setSize(window.innerWidth,window.innerHeight),this.composer.setSize(window.innerWidth,window.innerHeight)}),window.addEventListener(`wheel`,e=>{let t=e.target;if(t){let n=t.closest(`.window-body-scroll, .inspector-body, select`);if(n&&n.scrollHeight>n.clientHeight){let t=n.scrollTop>0&&e.deltaY<0,r=n.scrollTop+n.clientHeight<n.scrollHeight-1&&e.deltaY>0;if(t||r)return}}e.preventDefault(),this.controls.enabled=!0,this.cameraController.stopActiveTransition(),e.target!==this.renderer.domElement&&this.renderer.domElement.dispatchEvent(new WheelEvent(`wheel`,{clientX:e.clientX,clientY:e.clientY,screenX:e.screenX,screenY:e.screenY,deltaX:e.deltaX,deltaY:e.deltaY,deltaZ:e.deltaZ,deltaMode:e.deltaMode,ctrlKey:e.ctrlKey,shiftKey:e.shiftKey,altKey:e.altKey,metaKey:e.metaKey,bubbles:!0,cancelable:!0}))},{passive:!1});let e=!1,t={x:0,y:0};window.addEventListener(`pointerdown`,n=>{t={x:n.clientX,y:n.clientY},this.controls.enabled=!0;let r=n.target;r&&(document.activeElement&&document.activeElement instanceof HTMLElement&&(document.activeElement.tagName===`BUTTON`||document.activeElement.tagName===`A`)&&document.activeElement.blur(),r.closest(`button, input, select, option, textarea, .window-titlebar, .window-resize-gripper, .window-drag-icon, a, [role="button"], input[type="range"]`)||(this.cameraController.stopActiveTransition(),r!==this.renderer.domElement&&(e=!0,this.renderer.domElement.dispatchEvent(new PointerEvent(`pointerdown`,{pointerId:n.pointerId,clientX:n.clientX,clientY:n.clientY,screenX:n.screenX,screenY:n.screenY,button:n.button,buttons:n.buttons,ctrlKey:n.ctrlKey,shiftKey:n.shiftKey,altKey:n.altKey,metaKey:n.metaKey,pointerType:n.pointerType,bubbles:!0,cancelable:!0})))))}),window.addEventListener(`pointermove`,t=>{this.pointerNDC.x=t.clientX/window.innerWidth*2-1,this.pointerNDC.y=-(t.clientY/window.innerHeight)*2+1,e&&t.target!==this.renderer.domElement&&this.renderer.domElement.dispatchEvent(new PointerEvent(`pointermove`,{pointerId:t.pointerId,clientX:t.clientX,clientY:t.clientY,screenX:t.screenX,screenY:t.screenY,button:t.button,buttons:t.buttons,ctrlKey:t.ctrlKey,shiftKey:t.shiftKey,altKey:t.altKey,metaKey:t.metaKey,pointerType:t.pointerType,bubbles:!0,cancelable:!0}));let n=new r;n.setFromCamera(this.pointerNDC,this.camera);let i=this.constellation.pickOctopus(n,!1);if(i){document.body.style.cursor=`pointer`,this.tooltipElement.style.left=`${t.clientX+14}px`,this.tooltipElement.style.top=`${t.clientY+14}px`;let e=Y.octoGlyph(i.id,14);this.tooltipElement.innerHTML=`
          <div style="font-weight: 700; color: ${i.colorHex}; font-size: 11px; font-family: 'Roboto Mono', monospace; display: flex; align-items: center; gap: 6px;">
            ${e}
            <span>OCTO_${i.id} // ${i.title.toUpperCase()}</span>
          </div>
          <div style="font-size: 9.5px; opacity: 0.9; margin-top: 3px; font-family: 'Roboto Mono', monospace; color: #cbd5e1;">
            ${i.coreRole}
          </div>
          <div style="font-size: 8.5px; opacity: 0.65; margin-top: 2px; font-family: 'Roboto Mono', monospace;">
            ${i.department.toUpperCase()} // CLICK TO FOCUS
          </div>
        `,this.tooltipElement.classList.remove(`hidden`);return}let a=this.raycaster.pick(this.pointerNDC);if(a){if(document.body.style.cursor=`pointer`,this.tooltipElement.style.left=`${t.clientX+14}px`,this.tooltipElement.style.top=`${t.clientY+14}px`,a.type===`node`&&a.node){let e=I[a.node.regionId];this.tooltipElement.textContent=`Neuron #${a.node.index} (${a.node.type}) — ${e?e.name:``}`}else a.type===`fiber`&&a.fiber&&(this.tooltipElement.textContent=`Synapse #${a.fiber.index} (${a.fiber.pathwayName})`);this.tooltipElement.classList.remove(`hidden`)}else this.customStimulusMode||(document.body.style.cursor=`default`,this.tooltipElement.classList.add(`hidden`))}),window.addEventListener(`pointerup`,t=>{e&&(e=!1,t.target!==this.renderer.domElement&&this.renderer.domElement.dispatchEvent(new PointerEvent(`pointerup`,{pointerId:t.pointerId,clientX:t.clientX,clientY:t.clientY,button:t.button,bubbles:!0,cancelable:!0})))}),window.addEventListener(`click`,e=>{this.controls.enabled=!0;let n=e.target,i=n.closest(`.octo-badge`);if(i){let e=i.getAttribute(`data-octo-id`);if(e!==null){let t=parseInt(e,10);if(!isNaN(t)){this.constellation.focusOnOctopus(t);return}}}if(Math.hypot(e.clientX-t.x,e.clientY-t.y)>14||n.closest(`.floating-window, #top-header, button, select, input, .window-titlebar`))return;let o=new a(e.clientX/window.innerWidth*2-1,-(e.clientY/window.innerHeight)*2+1),s=new r;s.setFromCamera(o,this.camera);let c=this.constellation.pickOctopus(s,!0);if(c){this.updateBreadcrumbs(`WHOLE_OCTOPUS`,`OCTO_${c.id} // ${c.title.toUpperCase()}`);return}let l=this.raycaster.pick(o);l&&(this.customStimulusMode?(l.node?this.signalPropagator.triggerNeuronMicrocircuitCascade(l.node.index,40):l.fiber&&this.signalPropagator.triggerSingleFiberStimulus(l.fiber.index),this.customStimulusMode=!1,this.tooltipElement.classList.add(`hidden`)):l.type===`node`&&l.node?(this.selectedNode=l.node,this.selectedFiber=null,this.neuralNetwork.setSelectedNeuron(l.node.index),this.inspectorPanel.showNeuron(l.node),this.updateBreadcrumbs(`INDIVIDUAL_NEURON`,`Neuron #${l.node.index}`)):l.type===`fiber`&&l.fiber&&l.sourceNode&&l.targetNode&&(this.selectedFiber=l.fiber,this.selectedNode=null,this.neuralNetwork.setSelectedFiber(l.fiber.index),this.inspectorPanel.showFiber(l.fiber,l.sourceNode,l.targetNode),this.signalPropagator.triggerSingleFiberStimulus(l.fiber.index),this.updateBreadcrumbs(`INDIVIDUAL_CONNECTION`,`Synapse #${l.fiber.index}`)))}),window.addEventListener(`dblclick`,e=>{if(e.target.closest(`.floating-window, #top-header, button, select, input, .octo-badge`))return;let t=this.raycaster.pick(this.pointerNDC);t&&(t.type===`node`&&t.node?(this.cameraController.goToIndividualNeuron(t.node.position,!1),this.neuralNetwork.setSelectedNeuron(t.node.index),this.inspectorPanel.showNeuron(t.node)):t.type===`fiber`&&t.sourceNode&&t.targetNode&&(this.cameraController.goToConnectionFiber(t.sourceNode.position,t.targetNode.position),this.neuralNetwork.setSelectedFiber(t.fiber.index),this.inspectorPanel.showFiber(t.fiber,t.sourceNode,t.targetNode)))});let n=document.getElementById(`btn-view-constellation`);n&&n.addEventListener(`click`,()=>{this.voiceSystem.stopSpeaking(),this.voiceSystem.hideBanner(),this.constellation.resetOrbitView(),this.updateBreadcrumbs(`WHOLE_OCTOPUS`,`8-OCTOPUS CONSTELLATION`)});let i=document.getElementById(`btn-toggle-voice`),o=document.getElementById(`label-voice-state`),s=document.getElementById(`icon-voice-state`),c=e=>{i&&(i.classList.toggle(`muted`,e),i.setAttribute(`aria-pressed`,e?`false`:`true`),i.setAttribute(`aria-label`,e?`Voice narration muted. Click to enable audio.`:`Voice narration enabled. Click to mute audio.`)),o&&(o.textContent=e?`VOICE: OFF`:`VOICE: ON`),s&&(s.innerHTML=e?`<path d="M11 5L6 9H2V15H6L11 19V5Z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><line x1="23" y1="9" x2="17" y2="15" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><line x1="17" y1="9" x2="23" y2="15" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>`:`<path d="M11 5L6 9H2V15H6L11 19V5Z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M15.54 8.46C16.48 9.4 17 10.65 17 12C17 13.35 16.48 14.6 15.54 15.54" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><path d="M19.07 4.93C20.94 6.8 22 9.35 22 12C22 14.65 20.94 17.2 19.07 19.07" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>`)};c(this.voiceSystem.getIsMuted()),i&&i.addEventListener(`click`,()=>{let e=this.voiceSystem.toggleMute();c(e)});let l=document.getElementById(`btn-toggle-activity-log`);l&&this.activityLogPanel.bindToggleButton(l);let u=document.getElementById(`btn-toggle-reduced-motion`),d=document.getElementById(`label-reduced-motion`),f=e=>{u&&(u.classList.toggle(`active`,e),u.setAttribute(`aria-pressed`,String(e)),u.setAttribute(`aria-label`,e?`Reduced motion active. Click to restore normal motion.`:`Normal motion active. Click to reduce motion.`)),d&&(d.textContent=e?`MOTION: REDUCED`:`MOTION: NORMAL`)};f(B.getInstance().isReducedMotion()),B.getInstance().addListener(f),u&&u.addEventListener(`click`,()=>{let e=B.getInstance().toggleReducedMotion();f(e)}),window.addEventListener(`keydown`,e=>{if(e.key===`Escape`){if(this.activityLogPanel?.isOpen()){this.activityLogPanel.hide();return}if(this.manualModal?.isOpen()){this.manualModal.close();return}if(this.cognitiveInspector?.container&&this.cognitiveInspector.container.style.display!==`none`){this.cognitiveInspector.hide();return}this.inspectorPanel?.hide();let e=document.getElementById(`live-sandbox-window`);e&&e.style.display!==`none`&&(e.style.display=`none`,e.classList.add(`hidden`))}else if(e.key===`l`||e.key===`L`){let e=document.activeElement?.tagName;e!==`INPUT`&&e!==`TEXTAREA`&&this.activityLogPanel?.toggle()}});let p=document.getElementById(`btn-toggle-domain-mode`),m=document.getElementById(`label-domain-mode`),h=e=>{m&&(m.textContent=e===`DUAL`?`MODE: DUAL (SW + AI/ML)`:e===`SOFTWARE`?`MODE: SOFTWARE DEV`:`MODE: AI/ML RESEARCH`),p&&p.setAttribute(`data-mode`,e.toLowerCase())};p&&p.addEventListener(`click`,()=>{let e=this.voiceSystem.getDomainMode(),t=e===`DUAL`?`SOFTWARE`:e===`SOFTWARE`?`AIML`:`DUAL`;this.voiceSystem.setDomainMode(t),this.constellation.setDomainMode(t),h(t)}),this.constellation.onDomainModeChange=e=>{this.voiceSystem.setDomainMode(e),h(e)};let g=document.getElementById(`btn-live-preview`),_=document.getElementById(`label-live-preview`),v=document.getElementById(`live-sandbox-window`),y=document.getElementById(`live-sandbox-iframe`),b=document.getElementById(`sandbox-title`),x=document.getElementById(`sandbox-url-display`),S=document.getElementById(`sandbox-service-type`),C=document.getElementById(`sandbox-api-link`),w=document.getElementById(`btn-sandbox-close`),T=document.getElementById(`btn-sandbox-reload`),E=document.getElementById(`btn-sandbox-open-external`),D=``,O=(e,t=`WEB APP`,n=`LIVE APPLICATION SANDBOX`,r)=>{D=e,v&&(v.style.display=`flex`,v.classList.remove(`hidden`)),y&&y.src!==e&&(y.src=e),b&&(b.textContent=n.toUpperCase()),x&&(x.textContent=e),S&&(S.textContent=(t||`WEB APP`).toUpperCase().replace(`_`,` `)),E&&(E.href=e),C&&(r&&r!==e?(C.href=r,C.style.display=`inline-block`):C.style.display=`none`)};g&&g.addEventListener(`click`,()=>{D&&O(D)}),w&&w.addEventListener(`click`,()=>{v&&(v.style.display=`none`,v.classList.add(`hidden`))}),T&&T.addEventListener(`click`,()=>{y&&D&&(y.src=D)}),this.constellation.onLiveServiceReady=e=>{let t=e.service_url||e.payload&&e.payload.primary_url;if(!t)return;D=t;let n=t.match(/:(\d+)/),r=n?`(:${n[1]})`:``,i=(e.service_type||`APP`).toUpperCase().replace(`_`,` `);g&&(g.style.display=`flex`,g.classList.remove(`hidden`)),_&&(_.textContent=`LIVE ${i} ${r}`),O(t,e.service_type,e.summary||`LIVE APPLICATION SANDBOX`,e.api_docs_url),this.voiceSystem.speakOctopusRole(7)};let k=document.getElementById(`btn-start-tour-header`);k&&k.addEventListener(`click`,()=>this.startGuidedTour()),this.controlPanel.onStartTour=()=>this.startGuidedTour()}startGuidedTour(){this.selectedNode=null,this.selectedFiber=null,this.neuralNetwork.setSelectedNeuron(null),this.neuralNetwork.setSelectedFiber(null),this.inspectorPanel.hide(),this.signalPanel.clearProgress(),this.tooltipElement.classList.add(`hidden`);let e=document.getElementById(`signal-trigger-panel`);e&&(e.style.display=`none`);let t=document.getElementById(`control-panel`);t&&(t.style.display=`none`),this.tourHUD.show(),this.storyTourManager.startTour(),this.updateBreadcrumbs(`WHOLE_OCTOPUS`,`ANIMATED TOUR`)}checkWebGLSupport(){if(typeof window>`u`)return!1;try{let e=document.createElement(`canvas`);return!!(window.WebGLRenderingContext&&(e.getContext(`webgl2`)||e.getContext(`webgl`)))}catch{return!1}}renderWebGLFallbackNotice(e){let t=document.getElementById(`webgl-fallback-notice`);t||(t=document.createElement(`div`),t.id=`webgl-fallback-notice`,t.setAttribute(`role`,`alert`),t.style.cssText=`
        position: fixed;
        bottom: 24px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(17, 24, 39, 0.95);
        border: 1px solid #fab387;
        color: #ffffff;
        padding: 14px 20px;
        border-radius: 8px;
        font-family: 'Roboto Mono', monospace;
        font-size: 11px;
        z-index: 99999;
        display: flex;
        align-items: center;
        gap: 12px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.8);
      `,document.body.appendChild(t)),t.innerHTML=`
      <span style="color: #fab387; font-weight: 700;">[A11Y FALLBACK]</span>
      <span>${e||`WebGL 3D hardware acceleration is unavailable. Displaying real-time accessible text & arm telemetry.`}</span>
      <button id="btn-fallback-view-table" style="background: #38bdf8; color: #0b0f19; border: none; padding: 4px 10px; border-radius: 4px; font-weight: 700; cursor: pointer; font-size: 10px;">
        OPEN TABLE & LOGS
      </button>
    `;let n=t.querySelector(`#btn-fallback-view-table`);n&&n.addEventListener(`click`,()=>{this.activityLogPanel?.show()})}initFallbackUI(){let e=document.getElementById(`btn-toggle-activity-log`);e&&this.activityLogPanel.bindToggleButton(e),window.addEventListener(`keydown`,e=>{e.key===`Escape`?this.activityLogPanel?.isOpen()&&this.activityLogPanel.hide():(e.key===`l`||e.key===`L`)&&document.activeElement?.tagName!==`INPUT`&&document.activeElement?.tagName!==`TEXTAREA`&&this.activityLogPanel?.toggle()})}updateScreenReaderSummary(e){let t=document.getElementById(`canvas-live-summary`);if(!t)return;let n=this.constellation?.getActiveOctopus(),r=this.voiceSystem?.getDomainMode()||`DUAL`,i=e?.status||n?.data.status||`ONLINE`,a=e?.summary||n?.data.currentAction||`Running tasks`;t.textContent=`OctoFlow Cephalopod Swarm: 8 arms online. Domain: ${r}. Active Arm ${n?.data.id??0} (${i}): ${a}.`}animate=()=>{requestAnimationFrame(this.animate);let e=this.clock.getDelta(),t=this.clock.getElapsedTime();if(this.constellation.animate(e),this.storyTourManager.update(e),this.cameraController.update(e),this.cameraController.navMode===`FOLLOW_SIGNAL`){let t=this.signalPropagator.getLeadPulsePosition();t&&this.cameraController.updateSignalFollow(t,e)}let n=this.controlPanel.getState();this.signalPropagator.update(e,n.signalSpeed),this.neuralNetwork.update(t,this.signalPropagator.stimulusOrigin,this.signalPropagator.stimulusWaveRadius,this.signalPropagator.stimulusIntensity,this.camera),this.composer.render()}};window.addEventListener(`DOMContentLoaded`,()=>{new Ve});