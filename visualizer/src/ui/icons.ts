/** Custom Biological & Neurological Vector Glyphs (Apple VisionOS Pro Style).
 * Hand-crafted inline SVG icons with glowing neon gradients, translucent glass rings, and precise geometry.
 */

export const ICONS = {
  // 1. Octopus Core Logo (Cephalopod silhouette with neural nucleus)
  octopusCore: (size = 18, color = '#38bdf8') => `
    <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M12 2C7.5 2 4 5.5 4 10C4 13.2 5.8 15.8 8.5 17.2V20C8.5 20.8 9.2 21.5 10 21.5C10.8 21.5 11.5 20.8 11.5 20V18.5H12.5V20C12.5 20.8 13.2 21.5 14 21.5C14.8 21.5 15.5 20.8 15.5 20V17.2C18.2 15.8 20 13.2 20 10C20 5.5 16.5 2 12 2Z" stroke="${color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" fill="rgba(56, 189, 248, 0.12)"/>
      <circle cx="9" cy="9.5" r="1.5" fill="#ffffff" filter="drop-shadow(0 0 4px ${color})"/>
      <circle cx="15" cy="9.5" r="1.5" fill="#ffffff" filter="drop-shadow(0 0 4px ${color})"/>
      <path d="M10 13.5C11 14.5 13 14.5 14 13.5" stroke="${color}" stroke-width="1.4" stroke-linecap="round"/>
      <circle cx="12" cy="6" r="1" fill="#38bdf8" filter="drop-shadow(0 0 3px #38bdf8)"/>
    </svg>
  `,

  // 2. Vertical Lobe / Central Brain (Multi-lobed cortex with pulsing core)
  brainCortex: (size = 16, color = '#c084fc') => `
    <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M9.5 3C7 3 5 5 5 7.5C5 8.4 5.3 9.2 5.7 10C4.7 10.6 4 11.7 4 13C4 14.4 4.8 15.6 6 16.2C6 18.3 7.7 20 9.8 20C10.6 20 11.4 19.7 12 19.2C12.6 19.7 13.4 20 14.2 20C16.3 20 18 18.3 18 16.2C19.2 15.6 20 14.4 20 13C20 11.7 19.3 10.6 18.3 10C18.7 9.2 19 8.4 19 7.5C19 5 17 3 14.5 3C13.5 3 12.6 3.4 12 4C11.4 3.4 10.5 3 9.5 3Z" stroke="${color}" stroke-width="1.5" fill="rgba(192, 132, 252, 0.1)"/>
      <path d="M12 5V19" stroke="${color}" stroke-width="1.4" stroke-dasharray="2 2"/>
      <circle cx="9" cy="11" r="1.5" fill="#ffffff" filter="drop-shadow(0 0 4px ${color})"/>
      <circle cx="15" cy="11" r="1.5" fill="#ffffff" filter="drop-shadow(0 0 4px ${color})"/>
    </svg>
  `,

  // 3. Brachial Ring (8-Node Radial Interbrachial Network)
  brachialRing: (size = 16, color = '#38bdf8') => `
    <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <circle cx="12" cy="12" r="7.5" stroke="${color}" stroke-width="1.5" stroke-dasharray="3 2" fill="rgba(56, 189, 248, 0.08)"/>
      <circle cx="12" cy="4.5" r="1.8" fill="#ffffff" stroke="${color}" stroke-width="1.2"/>
      <circle cx="17.3" cy="6.7" r="1.8" fill="#ffffff" stroke="${color}" stroke-width="1.2"/>
      <circle cx="19.5" cy="12" r="1.8" fill="#ffffff" stroke="${color}" stroke-width="1.2"/>
      <circle cx="17.3" cy="17.3" r="1.8" fill="#ffffff" stroke="${color}" stroke-width="1.2"/>
      <circle cx="12" cy="19.5" r="1.8" fill="#ffffff" stroke="${color}" stroke-width="1.2"/>
      <circle cx="6.7" cy="17.3" r="1.8" fill="#ffffff" stroke="${color}" stroke-width="1.2"/>
      <circle cx="4.5" cy="12" r="1.8" fill="#ffffff" stroke="${color}" stroke-width="1.2"/>
      <circle cx="6.7" cy="6.7" r="1.8" fill="#ffffff" stroke="${color}" stroke-width="1.2"/>
      <circle cx="12" cy="12" r="2.2" fill="${color}" filter="drop-shadow(0 0 6px ${color})"/>
    </svg>
  `,

  // 4. Action Potential / Signal Wave
  actionPotential: (size = 16, color = '#facc15') => `
    <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M13 2L4 13.5H11.5L10 22L20 9.5H12.5L14 2H13Z" stroke="${color}" stroke-width="1.6" stroke-linejoin="round" fill="rgba(250, 204, 21, 0.15)" filter="drop-shadow(0 0 6px rgba(250, 204, 21, 0.5))"/>
    </svg>
  `,

  // 5. 360° Spatial Orbit Gimbal
  spatialOrbit: (size = 16, color = '#38bdf8') => `
    <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <circle cx="12" cy="12" r="8" stroke="${color}" stroke-width="1.4" stroke-opacity="0.5"/>
      <ellipse cx="12" cy="12" rx="8.5" ry="3.5" stroke="${color}" stroke-width="1.5" transform="rotate(-25 12 12)"/>
      <circle cx="12" cy="12" r="2" fill="#ffffff" filter="drop-shadow(0 0 5px ${color})"/>
    </svg>
  `,

  // 6. Neural Free Flight / Inside Network
  freeFlight: (size = 16, color = '#818cf8') => `
    <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M12 2L19 21L12 17L5 21L12 2Z" stroke="${color}" stroke-width="1.5" stroke-linejoin="round" fill="rgba(129, 140, 248, 0.12)"/>
      <circle cx="12" cy="11" r="1.5" fill="#ffffff"/>
    </svg>
  `,

  // 7. Sucker Mechanoreceptor / Touch Probe
  suckerReceptor: (size = 16, color = '#f43f5e') => `
    <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <circle cx="12" cy="10" r="7" stroke="${color}" stroke-width="1.5" fill="rgba(244, 63, 94, 0.12)"/>
      <circle cx="12" cy="10" r="3" stroke="${color}" stroke-width="1.3" fill="rgba(255, 255, 255, 0.3)"/>
      <path d="M12 17V22" stroke="${color}" stroke-width="1.6" stroke-linecap="round"/>
      <circle cx="12" cy="10" r="1.2" fill="#ffffff" filter="drop-shadow(0 0 4px #f43f5e)"/>
    </svg>
  `,

  // 8. Optic Tectum / Visual System
  opticLobe: (size = 16, color = '#a855f7') => `
    <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M2 12C2 12 5.5 5 12 5C18.5 5 22 12 22 12C22 12 18.5 19 12 19C5.5 19 2 12 2 12Z" stroke="${color}" stroke-width="1.5" fill="rgba(168, 85, 247, 0.1)"/>
      <circle cx="12" cy="12" r="3.5" stroke="${color}" stroke-width="1.4" fill="rgba(255, 255, 255, 0.2)"/>
      <circle cx="12" cy="12" r="1.5" fill="#ffffff" filter="drop-shadow(0 0 5px #a855f7)"/>
    </svg>
  `,

  // 9. Escape Jet Reflex
  escapeJet: (size = 16, color = '#f97316') => `
    <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M12 2V9M8 4L11 8M16 4L13 8" stroke="${color}" stroke-width="1.5" stroke-linecap="round"/>
      <path d="M6 10C6 10 7 17 12 22C17 17 18 10 18 10H6Z" stroke="${color}" stroke-width="1.5" fill="rgba(249, 115, 22, 0.15)"/>
      <circle cx="12" cy="14" r="1.8" fill="#ffffff"/>
    </svg>
  `,

  // 10. Custom Micro-Probe Crosshair
  customProbe: (size = 16, color = '#10b981') => `
    <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <circle cx="12" cy="12" r="8" stroke="${color}" stroke-width="1.4" stroke-dasharray="4 2"/>
      <path d="M12 2V6M12 18V22M2 12H6M18 12H22" stroke="${color}" stroke-width="1.5" stroke-linecap="round"/>
      <circle cx="12" cy="12" r="2" fill="#ffffff" filter="drop-shadow(0 0 4px ${color})"/>
    </svg>
  `,

  // 11. Connectome Mesh Lattice
  connectomeLattice: (size = 16, color = '#38bdf8') => `
    <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M12 2L20 7V17L12 22L4 17V7L12 2Z" stroke="${color}" stroke-width="1.4" fill="rgba(56, 189, 248, 0.08)"/>
      <path d="M12 2V22M4 7L20 17M4 17L20 7" stroke="${color}" stroke-width="1.2" stroke-opacity="0.4"/>
      <circle cx="12" cy="12" r="2" fill="#ffffff"/>
    </svg>
  `,

  // 12. Biological Oscilloscope / Neural Activity Wave
  activityWave: (size = 16, color = '#06b6d4') => `
    <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M2 13H6L8.5 5L12.5 19L15.5 9L18 13H22" stroke="${color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" filter="drop-shadow(0 0 4px ${color})"/>
    </svg>
  `,

  // 13. Explore Compass
  exploreCompass: (size = 16, color = '#38bdf8') => `
    <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <circle cx="12" cy="12" r="8" stroke="${color}" stroke-width="1.4"/>
      <path d="M14.5 9.5L10 11L9.5 14.5L14 13L14.5 9.5Z" fill="${color}" stroke="#ffffff" stroke-width="1"/>
    </svg>
  `,

  // 14. Anatomy Silhouette Layer
  anatomyLayer: (size = 16, color = '#ec4899') => `
    <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M12 3C9 3 7 5 7 8C7 10 8 11.5 9 12.5C7 13.5 5 15.5 5 18C5 19.5 6.5 21 8.5 21C10.5 21 11.5 19.5 12 18.5C12.5 19.5 13.5 21 15.5 21C17.5 21 19 19.5 19 18C19 15.5 17 13.5 15 12.5C16 11.5 17 10 17 8C17 5 15 3 12 3Z" stroke="${color}" stroke-width="1.4" fill="rgba(236, 72, 153, 0.12)"/>
    </svg>
  `,

  // 15. Guided Tour Play Glyph
  tourPlay: (size = 16, color = '#ffffff') => `
    <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <circle cx="12" cy="12" r="9" stroke="${color}" stroke-width="1.4" stroke-opacity="0.7"/>
      <path d="M10 8.5L16 12L10 15.5V8.5Z" fill="${color}"/>
    </svg>
  `,

  // 16. Scientific Concept / Insight Spark
  concept: (size = 16, color = '#facc15') => `
    <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M12 2C8.13 2 5 5.13 5 9C5 11.38 6.19 13.47 8 14.74V17C8 17.55 8.45 18 9 18H15C15.55 18 16 17.55 16 17V14.74C17.81 13.47 19 11.38 19 9C19 5.13 15.87 2 12 2Z" stroke="${color}" stroke-width="1.5" fill="rgba(250, 204, 21, 0.15)" filter="drop-shadow(0 0 4px rgba(250, 204, 21, 0.4))"/>
      <path d="M9 21H15" stroke="${color}" stroke-width="1.5" stroke-linecap="round"/>
      <path d="M10 10L12 8L14 10" stroke="#ffffff" stroke-width="1.2" stroke-linecap="round"/>
    </svg>
  `,

  // 17. Flow Arrow / Circuit Pointer
  flowArrow: (size = 12, color = 'rgba(255,255,255,0.4)') => `
    <svg width="${size}" height="${size}" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M6 3L11 8L6 13" stroke="${color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  `,

  // 18. Step Prev
  stepPrev: (size = 12, color = '#ffffff') => `
    <svg width="${size}" height="${size}" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M4 4V12M12 4L6 8L12 12V4Z" stroke="${color}" stroke-width="1.4" fill="${color}" stroke-linejoin="round"/>
    </svg>
  `,

  // 19. Step Next
  stepNext: (size = 12, color = '#ffffff') => `
    <svg width="${size}" height="${size}" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M12 4V12M4 4L10 8L4 12V4Z" stroke="${color}" stroke-width="1.4" fill="${color}" stroke-linejoin="round"/>
    </svg>
  `,

  // 20. Play
  play: (size = 12, color = '#ffffff') => `
    <svg width="${size}" height="${size}" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M5 3.5L13 8L5 12.5V3.5Z" fill="${color}"/>
    </svg>
  `,

  // 21. Pause
  pause: (size = 12, color = '#ffffff') => `
    <svg width="${size}" height="${size}" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M4.5 3.5H6.5V12.5H4.5V3.5ZM9.5 3.5H11.5V12.5H9.5V3.5Z" fill="${color}"/>
    </svg>
  `,

  // 22. Close Cross
  closeCross: (size = 12, color = 'rgba(255,255,255,0.7)') => `
    <svg width="${size}" height="${size}" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M3.5 3.5L12.5 12.5M12.5 3.5L3.5 12.5" stroke="${color}" stroke-width="1.6" stroke-linecap="round"/>
    </svg>
  `,

  // 23. Finish Flag / Complete
  finishFlag: (size = 12, color = '#10b981') => `
    <svg width="${size}" height="${size}" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <circle cx="8" cy="8" r="7" stroke="${color}" stroke-width="1.3" fill="rgba(16, 185, 129, 0.15)"/>
      <path d="M5 8L7 10L11 6" stroke="${color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  `,

  // 24. Drag Handle Gripper (6-dot matrix)
  dragGrip: (size = 14, color = 'rgba(255,255,255,0.6)') => `
    <svg width="${size}" height="${size}" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <circle cx="5" cy="4" r="1.3" fill="${color}"/>
      <circle cx="11" cy="4" r="1.3" fill="${color}"/>
      <circle cx="5" cy="8" r="1.3" fill="${color}"/>
      <circle cx="11" cy="8" r="1.3" fill="${color}"/>
      <circle cx="5" cy="12" r="1.3" fill="${color}"/>
      <circle cx="11" cy="12" r="1.3" fill="${color}"/>
    </svg>
  `,

  // 25. Window Minimize (Horizontal Dash)
  minimize: (size = 12, color = 'rgba(255,255,255,0.7)') => `
    <svg width="${size}" height="${size}" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <line x1="3" y1="8" x2="13" y2="8" stroke="${color}" stroke-width="1.8" stroke-linecap="round"/>
    </svg>
  `,

  // 26. Window Expand / Maximize (Square / Plus)
  maximize: (size = 12, color = 'rgba(255,255,255,0.7)') => `
    <svg width="${size}" height="${size}" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <rect x="3.5" y="3.5" width="9" height="9" rx="1.5" stroke="${color}" stroke-width="1.5"/>
    </svg>
  `,

  // 27. Reset Layout / Refresh Workspace
  resetLayout: (size = 14, color = '#74c7ec') => `
    <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
      <path d="M4 4V9H9" stroke="${color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M20 20V15H15" stroke="${color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M20 9A9 9 0 005.6 5.6L4 9" stroke="${color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M4 15A9 9 0 0018.4 18.4L20 15" stroke="${color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  `,

  // --- 8 CUSTOM CEPHALOPOD VECTOR GLYPHS (NO EMOJIS) ---
  octoArchitect: (size = 14, color = '#00F0FF') => `
    <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="octo-custom-glyph" style="display:inline-block;vertical-align:middle;">
      <path d="M12 2L21 7V17L12 22L3 17V7L12 2Z" stroke="${color}" stroke-width="1.8" stroke-linejoin="round" fill="rgba(0, 240, 255, 0.14)"/>
      <path d="M12 22V12M12 12L21 7M12 12L3 7" stroke="${color}" stroke-width="1.6" stroke-linejoin="round"/>
      <circle cx="12" cy="12" r="2.2" fill="#ffffff" filter="drop-shadow(0 0 4px ${color})"/>
    </svg>
  `,

  octoDatabase: (size = 14, color = '#A855F7') => `
    <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="octo-custom-glyph" style="display:inline-block;vertical-align:middle;">
      <ellipse cx="12" cy="5" rx="8" ry="3" stroke="${color}" stroke-width="1.8" fill="rgba(168, 85, 247, 0.22)"/>
      <path d="M4 5V12C4 13.65 7.58 15 12 15C16.42 15 20 13.65 20 12V5" stroke="${color}" stroke-width="1.8"/>
      <path d="M4 12V19C4 20.65 7.58 22 12 22C16.42 22 20 20.65 20 19V12" stroke="${color}" stroke-width="1.8"/>
      <circle cx="12" cy="12" r="1.4" fill="#ffffff"/>
      <circle cx="12" cy="19" r="1.4" fill="#ffffff"/>
    </svg>
  `,

  octoBackend: (size = 14, color = '#3B82F6') => `
    <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="octo-custom-glyph" style="display:inline-block;vertical-align:middle;">
      <path d="M13 2L3 14H12L11 22L21 10H12L13 2Z" stroke="${color}" stroke-width="1.8" stroke-linejoin="round" fill="rgba(59, 130, 246, 0.22)"/>
      <circle cx="12" cy="12" r="1.5" fill="#ffffff" filter="drop-shadow(0 0 4px ${color})"/>
    </svg>
  `,

  octoFrontend: (size = 14, color = '#EC4899') => `
    <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="octo-custom-glyph" style="display:inline-block;vertical-align:middle;">
      <rect x="3" y="4" width="18" height="16" rx="3" stroke="${color}" stroke-width="1.8" fill="rgba(236, 72, 153, 0.16)"/>
      <path d="M3 9H21" stroke="${color}" stroke-width="1.6"/>
      <circle cx="6.5" cy="6.5" r="1" fill="#ffffff"/>
      <circle cx="9.5" cy="6.5" r="1" fill="${color}"/>
      <path d="M8 15L11 12L8 9M13 16H17" stroke="#ffffff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  `,

  octoCognitive: (size = 14, color = '#10B981') => `
    <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="octo-custom-glyph" style="display:inline-block;vertical-align:middle;">
      <circle cx="12" cy="12" r="4" stroke="${color}" stroke-width="1.8" fill="rgba(16, 185, 129, 0.28)"/>
      <circle cx="12" cy="4" r="2" fill="${color}"/>
      <circle cx="20" cy="12" r="2" fill="${color}"/>
      <circle cx="12" cy="20" r="2" fill="${color}"/>
      <circle cx="4" cy="12" r="2" fill="${color}"/>
      <path d="M12 6V8M18 12H16M12 18V16M6 12H8" stroke="${color}" stroke-width="1.6"/>
      <circle cx="12" cy="12" r="1.8" fill="#ffffff" filter="drop-shadow(0 0 4px ${color})"/>
    </svg>
  `,

  octoSentinel: (size = 14, color = '#EF4444') => `
    <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="octo-custom-glyph" style="display:inline-block;vertical-align:middle;">
      <path d="M12 2L20 6V11C20 16.5 16.5 21 12 22C7.5 21 4 16.5 4 11V6L12 2Z" stroke="${color}" stroke-width="1.8" stroke-linejoin="round" fill="rgba(239, 68, 68, 0.2)"/>
      <circle cx="12" cy="11.5" r="2.4" fill="#ffffff" filter="drop-shadow(0 0 4px ${color})"/>
      <path d="M12 8V9M12 14V15" stroke="${color}" stroke-width="1.6" stroke-linecap="round"/>
    </svg>
  `,

  octoChaos: (size = 14, color = '#F59E0B') => `
    <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="octo-custom-glyph" style="display:inline-block;vertical-align:middle;">
      <ellipse cx="12" cy="12" rx="9" ry="3.5" stroke="${color}" stroke-width="1.5" transform="rotate(30 12 12)"/>
      <ellipse cx="12" cy="12" rx="9" ry="3.5" stroke="${color}" stroke-width="1.5" transform="rotate(-30 12 12)"/>
      <circle cx="12" cy="12" r="2.8" fill="#ffffff" filter="drop-shadow(0 0 5px ${color})"/>
    </svg>
  `,

  octoRunner: (size = 14, color = '#EAB308') => `
    <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="octo-custom-glyph" style="display:inline-block;vertical-align:middle;">
      <path d="M12 2L19 16L12 13L5 16L12 2Z" stroke="${color}" stroke-width="1.8" stroke-linejoin="round" fill="rgba(234, 179, 8, 0.22)"/>
      <path d="M12 13V22M9 19L12 22L15 19" stroke="${color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="12" cy="9" r="1.5" fill="#ffffff" filter="drop-shadow(0 0 4px ${color})"/>
    </svg>
  `,

  octoGlyph: (octoId: number, size = 14) => {
    switch (octoId) {
      case 0: return ICONS.octoArchitect(size, '#00F0FF');
      case 1: return ICONS.octoDatabase(size, '#A855F7');
      case 2: return ICONS.octoBackend(size, '#3B82F6');
      case 3: return ICONS.octoFrontend(size, '#EC4899');
      case 4: return ICONS.octoCognitive(size, '#10B981');
      case 5: return ICONS.octoSentinel(size, '#EF4444');
      case 6: return ICONS.octoChaos(size, '#F59E0B');
      case 7: return ICONS.octoRunner(size, '#EAB308');
      default: return ICONS.octopusCore(size, '#38bdf8');
    }
  },
};
