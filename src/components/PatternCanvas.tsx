import { Canvas } from "@react-three/fiber";
import { OrbitControls, Environment, ContactShadows } from "@react-three/drei";
import * as THREE from "three";
import type { CutPath, ZonedPatternConfig } from "../types/generator";

interface PatternCanvasProps {
    zonedPaths: CutPath[][];
    config: ZonedPatternConfig;
}

export function PatternCanvas({ zonedPaths, config }: PatternCanvasProps) {
    const surface = config.surface;

    // Only Circular surfaces have eccentricity/bore — Rectangular falls back to defaults
    const outerRadius = surface.type === "Circular" ? surface.outer_radius : 0;
    const innerRadius = surface.type === "Circular" ? surface.inner_radius : 0;
    const thickness   = surface.type === "Circular" ? surface.thickness   : (surface as any).thickness;
    const cx = surface.type === "Circular" ? surface.eccentricity_x : 0;
    const cy = surface.type === "Circular" ? surface.eccentricity_y : 0;

    // Camera distance auto-scales to workpiece size
    const camDist = Math.max(outerRadius * 6, 60);

    return (
        <div className="w-full h-full bg-zinc-900 border overflow-hidden relative">
            <Canvas
                camera={{ position: [cx, cy + outerRadius * 0.6, camDist], fov: 45 }}
                shadows
                gl={{ antialias: true, toneMapping: THREE.ACESFilmicToneMapping }}
            >
                {/* Lighting */}
                <ambientLight intensity={0.3} />
                <directionalLight position={[50, 50, 50]} intensity={1.2} castShadow
                    shadow-mapSize-width={2048} shadow-mapSize-height={2048} />
                <directionalLight position={[-30, 20, -30]} intensity={0.6} />
                <directionalLight position={[0, -20, -50]} intensity={0.8} color="#ffd700" />
                <pointLight position={[0, 50, 50]} intensity={0.5} color="#fff8dc" />

                <Environment preset="studio" />

                {/* ── Pattern paths — one group per zone ── */}
                {zonedPaths.map((zonePaths, zoneIndex) => {
                    const zoneColor = config.zones[zoneIndex]?.color ?? "#d4af37";
                    return (
                        <group key={zoneIndex}>
                            {zonePaths.map((path, pathIndex) => {
                                const points = path.points.map(
                                    (p) => new THREE.Vector3(p.x, p.y, p.z)
                                );
                                if (points.length < 2) return null;
                                const curve = new THREE.CatmullRomCurve3(points);
                                return (
                                    <mesh key={pathIndex} castShadow receiveShadow>
                                        <tubeGeometry args={[curve, points.length, 0.05, 6, false]} />
                                        <meshStandardMaterial
                                            color={zoneColor}
                                            metalness={0.95}
                                            roughness={0.15}
                                            envMapIntensity={1.5}
                                            emissive={zoneColor}
                                            emissiveIntensity={0.08}
                                        />
                                    </mesh>
                                );
                            })}
                        </group>
                    );
                })}

                {/* ── Workpiece disk — centred at eccentricity offset ── */}
                {surface.type === "Circular" && (
                    <mesh
                        position={[cx, cy, -thickness / 2]}
                        rotation={[Math.PI / 2, 0, 0]}
                        receiveShadow
                    >
                        <cylinderGeometry args={[outerRadius, outerRadius, thickness, 64]} />
                        <meshStandardMaterial
                            color="#2a2a2a"
                            metalness={0.7}
                            roughness={0.3}
                            opacity={0.85}
                            transparent
                        />
                    </mesh>
                )}

                {/* ── Bore — always at spindle origin (0,0) ── */}
                {surface.type === "Circular" && innerRadius > 0 && (
                    <mesh
                        position={[0, 0, -thickness / 2]}
                        rotation={[Math.PI / 2, 0, 0]}
                    >
                        {/* Slightly taller than workpiece so it's always visible */}
                        <cylinderGeometry args={[innerRadius, innerRadius, thickness + 0.2, 32]} />
                        <meshStandardMaterial
                            color="#0a0a0a"
                            metalness={0.1}
                            roughness={0.9}
                        />
                    </mesh>
                )}

                {/* ── Rectangular workpiece ── */}
                {surface.type === "Rectangular" && (
                    <mesh position={[0, 0, -(surface as any).thickness / 2]} receiveShadow>
                        <boxGeometry args={[(surface as any).width, (surface as any).height, (surface as any).thickness]} />
                        <meshStandardMaterial
                            color="#2a2a2a"
                            metalness={0.7}
                            roughness={0.3}
                            opacity={0.85}
                            transparent
                        />
                    </mesh>
                )}

                {/* Spindle axis indicator (thin post at origin) */}
                <mesh position={[0, 0, -thickness / 2]} rotation={[Math.PI / 2, 0, 0]}>
                    <cylinderGeometry args={[0.15, 0.15, thickness + 1, 12]} />
                    <meshStandardMaterial color="#ff4444" metalness={0.5} roughness={0.4} />
                </mesh>

                <ContactShadows
                    position={[cx, cy, -thickness - 1]}
                    opacity={0.4}
                    scale={Math.max(outerRadius * 3, 80)}
                    blur={2}
                    far={10}
                />

                <OrbitControls
                    makeDefault
                    enableDamping
                    dampingFactor={0.05}
                    target={[cx, cy, 0]}
                />

                <gridHelper
                    args={[Math.max(outerRadius * 4, 100), 20]}
                    rotation={[Math.PI / 2, 0, 0]}
                    position={[0, 0, -thickness - 1]}
                />
            </Canvas>
        </div>
    );
}
