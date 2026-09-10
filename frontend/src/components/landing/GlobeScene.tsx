import React, { useRef, useEffect } from 'react';
import * as THREE from 'three';
import type { AOIBounds } from '../../types/globe';

interface GlobeSceneProps {
  onAOISelect?: (bounds: AOIBounds) => void;
  selectedAOI?: AOIBounds | null;
}

// Convert lat/lng to 3D sphere coordinates
export function latLngToVec3(lat: number, lng: number, radius: number): THREE.Vector3 {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lng + 180) * (Math.PI / 180);
  return new THREE.Vector3(
    -radius * Math.sin(phi) * Math.cos(theta),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta)
  );
}

export const GlobeScene: React.FC<GlobeSceneProps> = ({ onAOISelect: _onAOISelect, selectedAOI: _selectedAOI }) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<{
    renderer: THREE.WebGLRenderer;
    scene: THREE.Scene;
    camera: THREE.PerspectiveCamera;
    earth: THREE.Mesh;
    animFrame: number;
    isDragging: boolean;
    prevMouse: { x: number; y: number };
    rotationVel: { x: number; y: number };
  } | null>(null);

  useEffect(() => {
    if (!mountRef.current) return;
    const mount = mountRef.current;
    const W = mount.clientWidth;
    const H = mount.clientHeight;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(W, H);
    renderer.setClearColor(0x000000, 0);
    mount.appendChild(renderer.domElement);

    // Scene & Camera
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, W / H, 0.1, 100);
    camera.position.set(0, 0, 2.8);

    // Lighting
    const ambient = new THREE.AmbientLight(0x334466, 1.2);
    scene.add(ambient);
    const sun = new THREE.DirectionalLight(0xffffff, 2.0);
    sun.position.set(5, 3, 5);
    scene.add(sun);

    // Stars background (static sphere texture)
    const starGeo = new THREE.SphereGeometry(50, 32, 32);
    const starMat = new THREE.MeshBasicMaterial({
      color: 0x020408,
      side: THREE.BackSide,
    });
    const stars = new THREE.Mesh(starGeo, starMat);
    scene.add(stars);
    // Add star points
    const starPositions = [];
    for (let i = 0; i < 2000; i++) {
      const v = new THREE.Vector3(
        (Math.random() - 0.5) * 90,
        (Math.random() - 0.5) * 90,
        (Math.random() - 0.5) * 90
      );
      if (v.length() > 20) {
        starPositions.push(v.x, v.y, v.z);
      }
    }
    const starPointGeo = new THREE.BufferGeometry();
    starPointGeo.setAttribute('position', new THREE.Float32BufferAttribute(starPositions, 3));
    const starPoints = new THREE.Points(
      starPointGeo,
      new THREE.PointsMaterial({ color: 0xaaccff, size: 0.08, transparent: true, opacity: 0.6 })
    );
    scene.add(starPoints);

    // Earth sphere (solid color + grid shader as placeholder before texture loads)
    const earthGeo = new THREE.SphereGeometry(1, 64, 64);

    // Atmospheric glow (additive blending outer sphere)
    const atmosphereGeo = new THREE.SphereGeometry(1.04, 32, 32);
    const atmosphereMat = new THREE.ShaderMaterial({
      uniforms: {},
      vertexShader: `
        varying vec3 vNormal;
        void main() {
          vNormal = normalize(normalMatrix * normal);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        varying vec3 vNormal;
        void main() {
          float intensity = pow(0.6 - dot(vNormal, vec3(0.0, 0.0, 1.0)), 2.0);
          gl_FragColor = vec4(0.0, 0.65, 0.95, intensity * 0.5);
        }
      `,
      blending: THREE.AdditiveBlending,
      side: THREE.FrontSide,
      transparent: true,
    });
    const atmosphere = new THREE.Mesh(atmosphereGeo, atmosphereMat);
    scene.add(atmosphere);

    // Load real NASA textures via Three.js TextureLoader
    const loader = new THREE.TextureLoader();
    const earthMat = new THREE.MeshPhongMaterial({
      color: 0x1a3a5c,
      emissive: 0x051015,
      shininess: 15,
    });
    const earth = new THREE.Mesh(earthGeo, earthMat);
    scene.add(earth);

    loader.load(
      'https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg',
      (tex) => {
        earthMat.map = tex;
        earthMat.color.set(0xffffff);
        earthMat.needsUpdate = true;
      }
    );

    // Orbit paths (3 elliptic rings)
    const orbitData = [
      { inclination: 51.6, color: 0x00d4ff, opacity: 0.35 },  // ISS
      { inclination: 98.0, color: 0x7c3aed, opacity: 0.25 },  // Polar (Sentinel)
      { inclination: 10.0, color: 0x0070f3, opacity: 0.20 },  // Near-equatorial
    ];
    orbitData.forEach(({ inclination, color, opacity }) => {
      const points: THREE.Vector3[] = [];
      for (let i = 0; i <= 128; i++) {
        const angle = (i / 128) * Math.PI * 2;
        points.push(new THREE.Vector3(Math.cos(angle) * 1.35, 0, Math.sin(angle) * 1.35));
      }
      const orbitGeo = new THREE.BufferGeometry().setFromPoints(points);
      const orbitMat = new THREE.LineBasicMaterial({ color, transparent: true, opacity });
      const orbit = new THREE.LineLoop(orbitGeo, orbitMat);
      orbit.rotation.x = (inclination * Math.PI) / 180;
      orbit.rotation.z = Math.random() * Math.PI;
      scene.add(orbit);

      // Satellite marker (small box)
      const satGeo = new THREE.BoxGeometry(0.02, 0.01, 0.02);
      const satMat = new THREE.MeshBasicMaterial({ color });
      const sat = new THREE.Mesh(satGeo, satMat);
      let t = Math.random();
      const animate = () => {
        t = (t + 0.001) % 1;
        const angle = t * Math.PI * 2;
        const localPos = new THREE.Vector3(Math.cos(angle) * 1.35, 0, Math.sin(angle) * 1.35);
        const matrix = new THREE.Matrix4().makeRotationX((inclination * Math.PI) / 180);
        matrix.multiply(new THREE.Matrix4().makeRotationZ(orbit.rotation.z));
        localPos.applyMatrix4(matrix);
        sat.position.copy(localPos);
      };
      (sat as any)._orbitAnimate = animate;
      scene.add(sat);
    });

    // Interaction state
    let isDragging = false;
    let prevMouse = { x: 0, y: 0 };
    let rotationVel = { x: 0, y: 0 };

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true;
      prevMouse = { x: e.clientX, y: e.clientY };
      rotationVel = { x: 0, y: 0 };
    };
    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      const dx = e.clientX - prevMouse.x;
      const dy = e.clientY - prevMouse.y;
      rotationVel.y = dx * 0.005;
      rotationVel.x = dy * 0.005;
      earth.rotation.y += rotationVel.y;
      earth.rotation.x = Math.max(-0.5, Math.min(0.5, earth.rotation.x + rotationVel.x));
      atmosphere.rotation.copy(earth.rotation);
      prevMouse = { x: e.clientX, y: e.clientY };
    };
    const onMouseUp = () => { isDragging = false; };

    // Touch support
    const onTouchStart = (e: TouchEvent) => {
      isDragging = true;
      prevMouse = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    };
    const onTouchMove = (e: TouchEvent) => {
      if (!isDragging) return;
      const dx = e.touches[0].clientX - prevMouse.x;
      const dy = e.touches[0].clientY - prevMouse.y;
      earth.rotation.y += dx * 0.005;
      earth.rotation.x = Math.max(-0.5, Math.min(0.5, earth.rotation.x + dy * 0.005));
      atmosphere.rotation.copy(earth.rotation);
      prevMouse = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    };

    // Scroll zoom
    const onWheel = (e: WheelEvent) => {
      camera.position.z = Math.max(1.6, Math.min(5, camera.position.z + e.deltaY * 0.002));
    };

    renderer.domElement.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    renderer.domElement.addEventListener('touchstart', onTouchStart);
    renderer.domElement.addEventListener('touchmove', onTouchMove);
    renderer.domElement.addEventListener('touchend', onMouseUp);
    renderer.domElement.addEventListener('wheel', onWheel, { passive: true });

    // Animation loop
    let animFrame: number = 0;
    const animate = () => {
      animFrame = requestAnimationFrame(animate);
      // Auto-rotate when idle
      if (!isDragging) {
        earth.rotation.y += 0.0008;
        atmosphere.rotation.y += 0.0008;
        // Dampen velocity
        rotationVel.x *= 0.92;
        rotationVel.y *= 0.92;
        earth.rotation.y += rotationVel.y;
        earth.rotation.x = Math.max(-0.5, Math.min(0.5, earth.rotation.x + rotationVel.x));
        atmosphere.rotation.copy(earth.rotation);
      }
      // Animate satellites
      scene.traverse((obj) => {
        if ((obj as any)._orbitAnimate) (obj as any)._orbitAnimate();
      });
      renderer.render(scene, camera);
    };
    animate();

    // Resize observer
    const resizeObs = new ResizeObserver(() => {
      const w = mount.clientWidth;
      const h = mount.clientHeight;
      renderer.setSize(w, h);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    });
    resizeObs.observe(mount);

    sceneRef.current = { renderer, scene, camera, earth, animFrame, isDragging, prevMouse, rotationVel };

    return () => {
      cancelAnimationFrame(animFrame);
      resizeObs.disconnect();
      renderer.domElement.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      renderer.dispose();
      if (mount.contains(renderer.domElement)) mount.removeChild(renderer.domElement);
    };
  }, []);

  return (
    <div
      ref={mountRef}
      className="absolute inset-0 cursor-grab active:cursor-grabbing"
      style={{ background: 'radial-gradient(ellipse at center, #050d1a 0%, #020408 70%)' }}
    />
  );
};
