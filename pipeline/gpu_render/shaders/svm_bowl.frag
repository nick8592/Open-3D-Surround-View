#version 330 core

out vec4 FragColor;

in vec2 TexCoord;
in vec3 FragPos;
in vec3 Normal;

// The 4 raw fisheye camera textures
uniform sampler2D textureFront;
uniform sampler2D textureBack;
uniform sampler2D textureLeft;
uniform sampler2D textureRight;

// The Look-Up Tables (LUTs) for mapping UVs to camera pixels
uniform sampler2D lutFront;
uniform sampler2D lutBack;
uniform sampler2D lutLeft;
uniform sampler2D lutRight;

// Alpha blending weights to merge the seams
uniform sampler2D blendMask;

// Basic lighting (Virtual Sun/Dome light for reflections/shading)
uniform vec3 viewPos; // Camera position

void main()
{
    // Fetch UV coordinates from the LUTs based on current bowl texture coordinate
    vec2 uvFront = texture(lutFront, TexCoord).rg;
    vec2 uvBack = texture(lutBack, TexCoord).rg;
    vec2 uvLeft = texture(lutLeft, TexCoord).rg;
    vec2 uvRight = texture(lutRight, TexCoord).rg;

    // Sample the actual camera textures using the mapped UVs
    vec4 colorFront = texture(textureFront, uvFront);
    vec4 colorBack = texture(textureBack, uvBack);
    vec4 colorLeft = texture(textureLeft, uvLeft);
    vec4 colorRight = texture(textureRight, uvRight);

    // Sample the blending weights
    vec4 weights = texture(blendMask, TexCoord);

    // Filter out black/empty patches if weight is strictly 0
    if (weights.r == 0.0) colorFront = vec4(0.0);
    if (weights.g == 0.0) colorBack = vec4(0.0);
    if (weights.b == 0.0) colorLeft = vec4(0.0);
    if (weights.a == 0.0) colorRight = vec4(0.0);

    // Blend the final base color based on the individual camera weights
    vec4 baseColor = (colorFront * weights.r) +
                     (colorBack * weights.g) +
                     (colorLeft * weights.b) +
                     (colorRight * weights.a);

    // Calculate basic lighting with the vertex normals
    vec3 norm = normalize(Normal);
    vec3 lightDir = normalize(vec3(0.0, 0.0, 10.0)); // Fake light from straight above
    
    // Ambient light
    float ambientStrength = 0.8;
    vec3 ambient = ambientStrength * vec3(1.0);
    
    // Diffuse light
    float diff = max(dot(norm, lightDir), 0.0);
    vec3 diffuse = diff * vec3(0.3);

    // Combine lighting with the texture base color
    vec3 finalRGB = (ambient + diffuse) * baseColor.rgb;

    FragColor = vec4(finalRGB, baseColor.a);
}
