/** Calibrated WebGL Shaders for Octopus Connectome (Clean, High-Contrast Scientific Aesthetic).
 * Delivers crisp neuron nodes, delicate filament fibers, and focused synaptic pulse highlights without over-blooming.
 */

export const NeuronParticleShader = {
  vertexShader: `
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
  `,

  fragmentShader: `
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
  `,
};

export const SynapticFiberShader = {
  vertexShader: `
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
  `,

  fragmentShader: `
    varying vec3 vColor;
    varying float vAlpha;

    void main() {
      gl_FragColor = vec4(vColor, vAlpha);
    }
  `,
};

export const ActionPotentialParticleShader = {
  vertexShader: `
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
  `,

  fragmentShader: `
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
  `,
};

export const SynapticPunctaShader = {
  vertexShader: `
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
  `,

  fragmentShader: `
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
  `,
};
