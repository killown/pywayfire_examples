from wayfire import WayfireSocket
from wayfire.extra.wpe import WPE 

sock = WayfireSocket()
wpe = WPE(sock)


border = """#version 300 es
@builtin_ext@
@builtin@

precision mediump float;

uniform sampler2D in_tex;
out vec4 out_color;
in mediump vec2 uvpos;

void main()
{
    vec4 c = get_pixel(uvpos);
    ivec2 size = textureSize(in_tex, 0);
    vec2 texelSize = 1.0 / vec2(size);
    vec4 border_color = vec4(0.0, 1.0, 0.0, 1.0);
    float border_size = 4.0;
    float corner_radius = 10.0;
    float d;
    // Sides
    if ((uvpos.x <= (texelSize.x * border_size) || uvpos.x >= 1.0 - (texelSize.x * border_size)) && uvpos.y > (texelSize.y * corner_radius) && uvpos.y < 1.0 - (texelSize.y * corner_radius) ||
        ((uvpos.y <= (texelSize.y * border_size) || uvpos.y >= 1.0 - (texelSize.y * border_size)) && uvpos.x > (texelSize.x * corner_radius) && uvpos.x < 1.0 - (texelSize.x * corner_radius)))
    {
        c = border_color;
    } else
    // Corners
    if (uvpos.x <= (texelSize.x * corner_radius) && uvpos.y <= (texelSize.y * corner_radius))
    {
        // Bottom Left
        d = distance(vec2(corner_radius), uvpos * vec2(size));
        if (d - corner_radius <= 0.0 && d - (corner_radius - border_size) >= 0.0)
        {
            c = border_color;
        }
    } else if (uvpos.x >= 1.0 - (texelSize.x * corner_radius) && uvpos.y <= (texelSize.y * corner_radius))
    {
        // Bottom Right
        d = distance(vec2(float(size.x) - corner_radius, corner_radius), uvpos * vec2(size));
        if (d - corner_radius <= 0.0 && d - (corner_radius - border_size) >= 0.0)
        {
            c = border_color;
        }
    } else if (uvpos.x <= (texelSize.x * corner_radius) && uvpos.y >= 1.0 - (texelSize.y * corner_radius))
    {
        // Top Left
        d = distance(vec2(corner_radius, float(size.y) - corner_radius), uvpos * vec2(size));
        if (d - corner_radius <= 0.0 && d - (corner_radius - border_size) >= 0.0)
        {
            c = border_color;
        }
    } else if (uvpos.x >= 1.0 - (texelSize.x * corner_radius) && uvpos.y >= 1.0 - (texelSize.y * corner_radius))
    {
        // Top Right
        d = distance(vec2(vec2(size) - corner_radius), uvpos * vec2(size));
        if (d - corner_radius <= 0.0 && d - (corner_radius - border_size) >= 0.0)
        {
            c = border_color;
        }
    }
    out_color = c;
}"""

border_path = "/tmp/border"
with open(border_path, "w") as file:
    file.write(border)


# will apply the border only for the focused view
id = sock.get_focused_view()["id"]

# apply the effect
wpe.filters_set_view_shader(id, border_path)
