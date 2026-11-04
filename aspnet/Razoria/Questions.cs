namespace Razoria;

/// <summary>An ASP.NET challenge: its options, the correct one (which must match an option exactly) and a short
/// explanation. tools/check-aspnet-questions.py builds every snippet as a real ASP.NET Core project, runs it, sends
/// it the requests in Send, and checks the answer against what really comes back, by Check:
///     body     the response's body, with its white space tidied ("(empty)" if there's none)
///     status   its status code
///     both     its status code, then its body
///     log      what the app wrote to its console
/// With several requests, their results are joined by spaces. A snippet starting with @page is Pages/Index.cshtml, in
/// an app that only maps its Razor Pages. "// --- name ---" lines split a snippet into the files they name.
/// CompileError is the code the build must fail with when the answer is that it doesn't compile, and Crash is the
/// exception that must end the app when the answer is that it crashes at startup.</summary>
public sealed record Question(string Prompt, string? Code, string[] Options, string Answer, string Explain)
{
    public string[] Send { get; init; } = [];
    public string Check { get; init; } = "";
    public string? CompileError { get; init; }
    public string? Crash { get; init; }
}

public static class Questions
{
    const string Crashes = "The app crashes at startup";

    static string[] Requests(string send) => send.Split(" then ");

    static string What(string send, string singular, string plural) =>
        send.Contains(" then ") ? $"What {plural} {send} get back, in order?" : $"What {singular} {send} get back?";

    static Question Make(string prompt, string send, string check, string code, string[] options, string answer, string explain) =>
        new(prompt, code.ReplaceLineEndings("\n"), options, answer, explain) { Send = Requests(send), Check = check };

    /// <summary>What's in the body of the response?</summary>
    static Question Body(string send, string code, string[] options, string answer, string explain) =>
        Make(What(send, "does", "do"), send, "body", code, options, answer, explain);

    /// <summary>What status code comes back?</summary>
    static Question Status(string send, string code, string[] options, string answer, string explain) =>
        Make(What(send, "status code does", "status codes do"), send, "status", code, options, answer, explain);

    /// <summary>What status code and body come back?</summary>
    static Question Both(string send, string code, string[] options, string answer, string explain) =>
        Make(What(send, "status code and body does", "status codes and bodies do"), send, "both", code, options, answer, explain);

    /// <summary>What does the app write to its console while it answers?</summary>
    static Question Log(string send, string code, string[] options, string answer, string explain) =>
        Make($"{send} arrives. What does the app write to its console?", send, "log", code, options, answer, explain);

    /// <summary>A Razor page, Pages/Index.cshtml: what does it send back?</summary>
    static Question Page(string send, string code, string[] options, string answer, string explain) =>
        Make($"This is Pages/Index.cshtml. What does {send} get back?", send, "body", code, options, answer, explain);

    static Question Ask(string prompt, string[] options, string answer, string explain) =>
        new(prompt, null, options, answer, explain);

    public static readonly Dictionary<string, Question[]> Levels = new()
    {
        ["easy"] =
        [
            Body("GET /hello", """
                var app = WebApplication.Create(args);
                app.MapGet("/hello", () => "Hello, Razoria!");
                app.Run();
                """, ["Hello, Razoria!", "\"Hello, Razoria!\"", "/hello", "(empty)"], "Hello, Razoria!",
                "MapGet ties a GET to a path. A string returned from an endpoint is sent as plain text, just as it is."),
            Status("GET /goodbye", """
                var app = WebApplication.Create(args);
                app.MapGet("/hello", () => "Hi");
                app.Run();
                """, ["200 OK", "302 Found", "404 Not Found", "500 Internal Server Error"], "404 Not Found",
                "No endpoint matches /goodbye, and nothing else answers it, so the pipeline ends with a 404."),
            Body("GET /hi/Ada", """
                var app = WebApplication.Create(args);
                app.MapGet("/hi/{name}", (string name) => $"Hi {name}");
                app.Run();
                """, ["Hi Ada", "Hi {name}", "Hi name", "(empty)"], "Hi Ada",
                "{name} in the route catches that part of the path, and a parameter of the same name receives it."),
            Body("GET /hi?name=Ada", """
                var app = WebApplication.Create(args);
                app.MapGet("/hi", (string name) => $"Hi {name}");
                app.Run();
                """, ["Hi Ada", "Hi ", "Hi name=Ada", "(empty)"], "Hi Ada",
                "A simple parameter that isn't in the route is looked for in the query string."),
            Status("POST /hello", """
                var app = WebApplication.Create(args);
                app.MapGet("/hello", () => "Hi");
                app.Run();
                """, ["200 OK", "400 Bad Request", "404 Not Found", "405 Method Not Allowed"], "405 Method Not Allowed",
                "The path matches, but only for GET. Routing can tell the difference, so it says 405, not 404."),
            Ask("In a new ASP.NET Core web app, where do you build the app and its pipeline?",
                ["Program.cs", "Global.asax", "web.config", "Default.aspx"], "Program.cs",
                "Program.cs holds them all, with top-level statements. Global.asax and Default.aspx belong to the older ASP.NET."),
            Page("GET /", """
                @page
                @{ var name = "Ada"; }
                <p>Hello @name</p>
                """, ["<p>Hello Ada</p>", "<p>Hello @name</p>", "<p>Hello name</p>", "Hello Ada"], "<p>Hello Ada</p>",
                "@{ } holds C#, and @name writes that variable's value into the HTML around it."),
            Ask("In a Razor file, which character switches from HTML to C#?",
                ["@", "#", "$", "%"], "@",
                "@ starts a Razor expression or code block. Everything else is taken to be plain HTML."),
            Page("GET /", """
                @page
                @{ int x = 2; }
                <p>@x + 3</p>
                <p>@(x + 3)</p>
                """, ["<p>5</p> <p>5</p>", "<p>2 + 3</p> <p>5</p>", "<p>@x + 3</p> <p>5</p>", "<p>2 + 3</p> <p>2 + 3</p>"],
                "<p>2 + 3</p> <p>5</p>",
                "A plain @ takes as little as it can, here just x. To do sums in the output, wrap them in @( )."),
            Body("GET /", """
                var app = WebApplication.Create(args);
                app.MapGet("/", () => new { Name = "Ada", Level = 3 });
                app.Run();
                """, ["{\"Name\":\"Ada\",\"Level\":3}", "{\"name\":\"Ada\",\"level\":3}", "{ Name = Ada, Level = 3 }", "name=Ada&level=3"],
                "{\"name\":\"Ada\",\"level\":3}",
                "An object is sent as JSON, and ASP.NET Core's JSON turns its property names into camelCase."),
            Status("GET /", """
                var app = WebApplication.Create(args);
                app.MapGet("/", () => Results.NoContent());
                app.Run();
                """, ["200 OK", "204 No Content", "404 Not Found", "500 Internal Server Error"], "204 No Content",
                "Results has a method for each usual response, and NoContent means success with nothing to send: 204."),
            Ask("Which command creates a new, empty ASP.NET Core project?",
                ["dotnet new web", "dotnet create aspnet", "aspnet new site", "npm init aspnet"], "dotnet new web",
                "dotnet new makes projects from templates. web is the empty one; webapp has Razor Pages and mvc has controllers."),
            Page("GET /", """
                @page
                @foreach (var n in new[] { 1, 2, 3 })
                {
                    <b>@n</b>
                }
                """, ["<b>1</b> <b>2</b> <b>3</b>", "<b>n</b> <b>n</b> <b>n</b>", "<b>@n</b>", "<b>3</b>"],
                "<b>1</b> <b>2</b> <b>3</b>",
                "Razor knows @foreach is C#, and that the tag inside it is HTML again, with @n going back to C# for a moment."),
            Page("GET /", """
                @page
                <p>A</p>
                @* <p>B</p> *@
                <!-- <p>C</p> -->
                """, ["<p>A</p>", "<p>A</p> <p>B</p> <p>C</p>", "<p>A</p> <!-- <p>C</p> -->", "<p>A</p> @* <p>B</p> *@"],
                "<p>A</p> <!-- <p>C</p> -->",
                "@* *@ is Razor's own comment and never leaves the server. An HTML comment is sent on to the browser like any other HTML."),
            Page("GET /", """
                @page
                @{ var tag = "<b>Hi</b>"; }
                <p>@tag</p>
                """, ["<p><b>Hi</b></p>", "<p>&lt;b&gt;Hi&lt;/b&gt;</p>", "<p>Hi</p>", "<p>@tag</p>"],
                "<p>&lt;b&gt;Hi&lt;/b&gt;</p>",
                "Razor encodes everything @ writes, so text can't turn into tags. That's what keeps a page safe from script injection."),
            Page("GET /", """
                @page
                <p>me@site.com owes @@5</p>
                """, ["<p>me@site.com owes @5</p>", "<p>me@site.com owes @@5</p>", "<p>mesite.com owes 5</p>", "Compile error"],
                "<p>me@site.com owes @5</p>",
                "Razor recognizes an email address and leaves it alone, and @@ writes one literal @."),
            Body("GET /", """
                // --- appsettings.json ---
                { "Realm": { "Name": "Razoria" } }
                // --- Program.cs ---
                var app = WebApplication.Create(args);
                app.MapGet("/", (IConfiguration config) => config["Realm:Name"]);
                app.Run();
                """, ["Razoria", "(empty)", "Realm:Name", "{ \"Name\": \"Razoria\" }"], "Razoria",
                "appsettings.json is loaded for you, and a colon steps down into a section: Realm, then Name."),
            Body("GET /", """
                var app = WebApplication.Create(args);
                app.MapGet("/", (IWebHostEnvironment env) => env.EnvironmentName);
                app.Run();
                """, ["Development", "Staging", "Production", "(empty)"], "Production",
                "With nothing setting ASPNETCORE_ENVIRONMENT, an app runs as Production. Development is only set for you by tools such as launchSettings.json."),
            Status("GET /", """
                var app = WebApplication.Create(args);
                app.MapGet("/", () => Results.Redirect("/new"));
                app.Run();
                """, ["200 OK", "301 Moved Permanently", "302 Found", "404 Not Found"], "302 Found",
                "Redirect is temporary, 302, unless you pass permanent: true, which makes it 301."),
            Ask("Which file extension did pages have in ASP.NET's first page framework, Web Forms?",
                [".aspx", ".asp", ".cshtml", ".razor"], ".aspx",
                ".asp was classic ASP, before .NET. .cshtml is Razor, and .razor is a Blazor component."),
        ],
        ["medium"] =
        [
            Log("GET /", """
                var app = WebApplication.Create(args);
                app.Use(async (ctx, next) =>
                {
                    Console.Write("A ");
                    await next();
                    Console.Write("C ");
                });
                app.MapGet("/", () =>
                {
                    Console.Write("B ");
                    return "ok";
                });
                app.Run();
                """, ["A B C", "A C B", "B A C", "A B"], "A B C",
                "Middleware wraps what comes after it: code before next() runs on the way in, and code after it on the way out."),
            Body("GET /", """
                var app = WebApplication.Create(args);
                app.Use(async (ctx, next) =>
                {
                    await ctx.Response.WriteAsync("1");
                    await next();
                });
                app.Run(ctx => ctx.Response.WriteAsync("2"));
                app.Use(async (ctx, next) =>
                {
                    await ctx.Response.WriteAsync("3");
                    await next();
                });
                app.Run();
                """, ["1", "12", "123", "13"], "12",
                "app.Run with a handler ends the pipeline: it has no next. Whatever is added after it never runs."),
            Body("GET /closed", """
                var app = WebApplication.Create(args);
                app.Use(async (ctx, next) =>
                {
                    if (ctx.Request.Path == "/closed")
                    {
                        await ctx.Response.WriteAsync("Keep out");
                        return;
                    }
                    await next();
                });
                app.MapGet("/closed", () => "Come in");
                app.Run();
                """, ["Keep out", "Come in", "Keep outCome in", "(empty)"], "Keep out",
                "A middleware that doesn't call next() short-circuits: nothing later in the pipeline runs, not even the endpoint."),
            Body("GET / then GET /", """
                var builder = WebApplication.CreateBuilder(args);
                builder.Services.AddSingleton<Counter>();
                var app = builder.Build();
                app.MapGet("/", (Counter c) => ++c.Value);
                app.Run();

                class Counter { public int Value; }
                """, ["1 1", "1 2", "0 1", "2 2"], "1 2",
                "A singleton is made once and shared by every request for as long as the app runs, so the count carries on."),
            Body("GET / then GET /", """
                var builder = WebApplication.CreateBuilder(args);
                builder.Services.AddScoped<Counter>();
                var app = builder.Build();
                app.MapGet("/", (Counter c) => ++c.Value);
                app.Run();

                class Counter { public int Value; }
                """, ["1 1", "1 2", "0 0", "2 2"], "1 1",
                "A scoped service is made once per request, so each request starts with a new Counter."),
            Body("GET /", """
                var builder = WebApplication.CreateBuilder(args);
                builder.Services.AddTransient<Rune>();
                var app = builder.Build();
                app.MapGet("/", (Rune a, Rune b) => ReferenceEquals(a, b));
                app.Run();

                class Rune { }
                """, ["true", "false", "Rune Rune", "(empty)"], "false",
                "A transient service is made new every time it's asked for, even twice in the same request."),
            Status("GET /items/abc", """
                var app = WebApplication.Create(args);
                app.MapGet("/items/{id}", (int id) => $"Item {id}");
                app.Run();
                """, ["200 OK", "400 Bad Request", "404 Not Found", "500 Internal Server Error"], "400 Bad Request",
                "The route matched, as {id} takes anything. Then abc couldn't be bound to an int, so the request is bad: 400."),
            Status("GET /items/abc", """
                var app = WebApplication.Create(args);
                app.MapGet("/items/{id:int}", (int id) => $"Item {id}");
                app.Run();
                """, ["200 OK", "400 Bad Request", "404 Not Found", "500 Internal Server Error"], "404 Not Found",
                "{id:int} is a route constraint, so abc doesn't match the route at all: not bad, just not found."),
            Ask("What does Page.IsPostBack tell a Web Forms page?",
                ["Whether this request is the page's own form coming back", "Whether the browser pressed Back",
                 "Whether the user is signed in", "Whether the page is cached"],
                "Whether this request is the page's own form coming back",
                "A Web Forms page posts back to itself, and Page_Load usually sets up its controls only when IsPostBack is false."),
            Body("POST /users {\"name\":\"Ada\"}", """
                var app = WebApplication.Create(args);
                app.MapPost("/users", (User user) => user.Name.ToUpper());
                app.Run();

                record User(string Name);
                """, ["ADA", "Ada", "{\"name\":\"Ada\"}", "(empty)"], "ADA",
                "A complex type is read from the JSON body. Names match whatever their capitals, so name fills Name."),
            Page("GET /", """
                @page
                @functions {
                    public string Word { get; set; } = "";
                    public void OnGet() => Word = "Hello";
                }
                <p>@Word</p>
                """, ["<p></p>", "<p>Hello</p>", "<p>Word</p>", "<p>OnGet</p>"], "<p>Hello</p>",
                "A Razor Page runs its OnGet handler for a GET, before the page renders. Here the page is its own model."),
            Page("GET /Ada", """
                @page "{name}"
                <p>@RouteData.Values["name"]</p>
                """, ["<p>Ada</p>", "<p>name</p>", "<p>Index</p>", "<p></p>"], "<p>Ada</p>",
                "A template after @page adds to the page's route, so /Ada reaches Index with name set to Ada."),
            Status("POST /", """
                @page
                @functions {
                    public void OnPost() { }
                }
                <form method="post"><button>Go</button></form>
                """, ["200 OK", "302 Found", "400 Bad Request", "405 Method Not Allowed"], "400 Bad Request",
                "Razor Pages check an antiforgery token on every POST. This request came without the one the form would have sent."),
            Page("GET /", """
                @page
                @addTagHelper *, Microsoft.AspNetCore.Mvc.TagHelpers
                <a asp-page="/Index">Home</a>
                """, ["<a href=\"/\">Home</a>", "<a href=\"/Index\">Home</a>", "<a asp-page=\"/Index\">Home</a>", "<a>Home</a>"],
                "<a href=\"/\">Home</a>",
                "The anchor tag helper works out the real address from routing, and Index's address is simply /."),
            Page("GET /", """
                @page
                @{ var tag = "<b>Hi</b>"; }
                <p>@Html.Raw(tag)</p>
                """, ["<p><b>Hi</b></p>", "<p>&lt;b&gt;Hi&lt;/b&gt;</p>", "<p>Hi</p>", "<p>Html.Raw(tag)</p>"], "<p><b>Hi</b></p>",
                "Html.Raw turns off Razor's encoding for this one value. Never hand it anything a visitor typed."),
            Ask("What hidden field carried a Web Forms page's control state between postbacks?",
                ["__VIEWSTATE", "__SESSION", "__RequestVerificationToken", "__POSTDATA"], "__VIEWSTATE",
                "ViewState made a stateless web feel like a desktop form, at the price of carrying it all in every page."),
            Ask("Which must come first in the pipeline?",
                ["UseAuthentication", "UseAuthorization", "Either: their order doesn't matter", "Neither: they replace each other"],
                "UseAuthentication",
                "Authentication works out who someone is, and authorization decides what they may do. It can't do that without knowing who."),
            Body("GET /doors/7", """
                using Microsoft.AspNetCore.Mvc;

                var builder = WebApplication.CreateBuilder(args);
                builder.Services.AddControllers();
                var app = builder.Build();
                app.MapControllers();
                app.Run();

                [ApiController]
                [Route("[controller]")]
                public class DoorsController : ControllerBase
                {
                    [HttpGet("{id}")]
                    public string Get(int id) => $"Door {id}";
                }
                """, ["Door 7", "Doors 7", "Door {id}", "(empty)"], "Door 7",
                "[controller] stands for the class's name without Controller, so its route is /doors, and {id} adds the rest."),
            Body("GET /", """
                using Microsoft.Extensions.Options;

                var builder = WebApplication.CreateBuilder(args);
                builder.Services.Configure<Realm>(o => o.Name = "Razoria");
                var app = builder.Build();
                app.MapGet("/", (IOptions<Realm> realm) => realm.Value.Name);
                app.Run();

                class Realm { public string Name { get; set; } = ""; }
                """, ["Razoria", "(empty)", "Realm", "IOptions<Realm>"], "Razoria",
                "That's the options pattern: Configure sets up a Realm, and IOptions<Realm> hands it over in .Value."),
            Body("GET / then GET /", """
                var builder = WebApplication.CreateBuilder(args);
                builder.Services.AddDistributedMemoryCache();
                builder.Services.AddSession();
                var app = builder.Build();
                app.UseSession();
                app.MapGet("/", (HttpContext ctx) =>
                {
                    int visits = (ctx.Session.GetInt32("visits") ?? 0) + 1;
                    ctx.Session.SetInt32("visits", visits);
                    return visits;
                });
                app.Run();
                """, ["1 1", "1 2", "0 1", "2 2"], "1 2",
                "The session cookie identifies the visitor, and what's stored for them on the server is still there next time."),
        ],
        ["hard"] =
        [
            Body("GET /users/me", """
                var app = WebApplication.Create(args);
                app.MapGet("/users/{id}", (string id) => $"user {id}");
                app.MapGet("/users/me", () => "myself");
                app.Run();
                """, ["user me", "myself", "user me myself", "(empty)"], "myself",
                "Routes aren't tried in the order they were added. The most specific match wins, and a literal beats a parameter."),
            Ask("In classic ASP.NET, which web.config setting shows the Yellow Screen's full details only to someone on the server itself?",
                ["<customErrors mode=\"RemoteOnly\" />", "<compilation debug=\"true\" />", "<trace enabled=\"true\" />", "<httpErrors existingResponse=\"Auto\" />"],
                "<customErrors mode=\"RemoteOnly\" />",
                "On means everyone gets a friendly page, Off means everyone sees the details, and RemoteOnly splits them, which was the default."),
            Status("GET /", """
                var app = WebApplication.Create(args);
                app.MapGet("/", () => "first");
                app.MapGet("/", () => "second");
                app.Run();
                """, ["200 OK", "404 Not Found", "405 Method Not Allowed", "500 Internal Server Error"], "500 Internal Server Error",
                "The two routes are equally specific, so neither can win. Routing throws an AmbiguousMatchException, and that's a 500."),
            Log("GET /", """
                using Microsoft.AspNetCore.Mvc;
                using Microsoft.AspNetCore.Mvc.Filters;

                var builder = WebApplication.CreateBuilder(args);
                builder.Services.AddControllers();
                var app = builder.Build();
                app.MapControllers();
                app.Run();

                [Route("/"), Log("class")]
                public class HomeController : ControllerBase
                {
                    [HttpGet, Log("method")]
                    public string Get()
                    {
                        Console.Write("action ");
                        return "ok";
                    }
                }

                public class LogAttribute(string name) : ActionFilterAttribute
                {
                    public override void OnActionExecuting(ActionExecutingContext _) =>
                        Console.Write($"{name}-in ");
                    public override void OnActionExecuted(ActionExecutedContext _) =>
                        Console.Write($"{name}-out ");
                }
                """, ["class-in method-in action method-out class-out", "method-in class-in action class-out method-out",
                      "class-in method-in action class-out method-out", "method-in class-in action method-out class-out"],
                "class-in method-in action method-out class-out",
                "Filters nest like middleware: the widest scope goes in first and comes out last, so the class's wraps the method's."),
            Ask("A singleton background service needs a scoped DbContext. What should it ask for in its constructor?",
                ["IServiceScopeFactory, to make a scope for each piece of work", "The DbContext itself", "HttpContext.RequestServices", "A static DbContext"],
                "IServiceScopeFactory, to make a scope for each piece of work",
                "Taking the DbContext itself would hold one instance for the app's whole life. There's no request, and so no HttpContext, in a background service."),
            Ask("Which transport does SignalR try first, if the client and server both support it?",
                ["WebSockets", "Server-Sent Events", "Long Polling", "gRPC"], "WebSockets",
                "It negotiates down from there: WebSockets, then Server-Sent Events, then Long Polling. A Hub's code stays the same whichever it gets."),
            Page("GET /", """
                @page
                @for (int i = 0; i < 2; i++)
                {
                    @:i=@i
                }
                """, ["i=0 i=1", "i=@i i=@i", "@:i=0 @:i=1", "Compile error"], "i=0 i=1",
                "Inside a code block, Razor expects C#. @: says that the rest of the line is text, with no tag needed around it."),
            Status("GET /", """
                // --- Pages/_Layout.cshtml ---
                <h1>@RenderSection("Title")</h1>
                @RenderBody()
                // --- Pages/Index.cshtml ---
                @page
                @{ Layout = "_Layout"; }
                <p>Body</p>
                """, ["200 OK", "204 No Content", "404 Not Found", "500 Internal Server Error"], "500 Internal Server Error",
                "A section is required unless you say required: false. This page doesn't define Title, so rendering it throws."),
            Ask("Which of these is still there on the next request, after a redirect?",
                ["TempData", "ViewData", "ViewBag", "@section"], "TempData",
                "ViewData and ViewBag live only as long as one request. TempData is kept until something reads it, for just this."),
            Body("GET /?page=3", """
                var app = WebApplication.Create(args);
                app.MapGet("/", ([AsParameters] Paging p) => p.Page * p.Size);
                app.Run();

                record struct Paging(int Page = 1, int Size = 10);
                """, ["3", "10", "30", "400"], "30",
                "[AsParameters] binds each of the type's parts as if it were a parameter: page comes from the query, and Size keeps its default."),
            Body("GET /a then GET /b", """
                var app = WebApplication.Create(args);
                app.MapGet("/a", () => "x");
                app.MapGet("/b", () => Results.Ok("x"));
                app.Run();
                """, ["x x", "x \"x\"", "\"x\" \"x\"", "\"x\" x"], "x \"x\"",
                "A string returned directly is plain text. Results.Ok writes its value as JSON, and a JSON string has quotes."),
            Body("GET /?a=1&b=1", """
                var app = WebApplication.Create(args);
                app.UseWhen(ctx => ctx.Request.Query.ContainsKey("a"), branch =>
                    branch.Use(async (ctx, next) =>
                    {
                        await ctx.Response.WriteAsync("use ");
                        await next();
                    }));
                app.MapWhen(ctx => ctx.Request.Query.ContainsKey("b"), branch =>
                    branch.Run(ctx => ctx.Response.WriteAsync("map ")));
                app.Run(ctx => ctx.Response.WriteAsync("end"));
                app.Run();
                """, ["use map", "use map end", "map end", "use end"], "use map",
                "UseWhen's branch rejoins the main pipeline afterwards. MapWhen's doesn't: once a request has gone down it, it never comes back."),
            Status("GET /", """
                using System.Security.Claims;

                var builder = WebApplication.CreateBuilder(args);
                builder.Services.AddAuthentication().AddBearerToken();
                builder.Services.AddAuthorization();
                var app = builder.Build();
                app.Use(async (ctx, next) =>
                {
                    var ada = new Claim(ClaimTypes.Name, "Ada");
                    ctx.User = new(new ClaimsIdentity([ada], "Test"));
                    await next();
                });
                app.UseAuthorization();
                app.MapGet("/", () => "Vault")
                    .RequireAuthorization(p => p.RequireRole("Keeper"));
                app.Run();
                """, ["200 OK", "401 Unauthorized", "403 Forbidden", "404 Not Found"], "403 Forbidden",
                "401 means we don't know who you are. Here Ada is known, and just isn't a Keeper, and that's 403."),
            Status("GET /vault/door then GET /vault/gold", """
                var builder = WebApplication.CreateBuilder(args);
                builder.Services.AddAuthentication().AddBearerToken();
                builder.Services.AddAuthorization();
                var app = builder.Build();
                var vault = app.MapGroup("/vault").RequireAuthorization();
                vault.MapGet("/door", () => "Door").AllowAnonymous();
                vault.MapGet("/gold", () => "Gold");
                app.Run();
                """, ["200 200", "200 401", "401 200", "401 401"], "200 401",
                "A group's settings reach every endpoint in it, but AllowAnonymous overrides any requirement around it."),
            Status("GET /", """
                // --- wwwroot/index.html ---
                <h1>Razoria</h1>
                // --- Program.cs ---
                var app = WebApplication.Create(args);
                app.UseStaticFiles();
                app.UseDefaultFiles();
                app.Run();
                """, ["200 OK", "301 Moved Permanently", "403 Forbidden", "404 Not Found"], "404 Not Found",
                "UseDefaultFiles only rewrites / to /index.html, for UseStaticFiles to serve. Here it comes too late, and no one's left to serve it."),
            Status("POST /orders {}", """
                using System.ComponentModel.DataAnnotations;
                using Microsoft.AspNetCore.Mvc;

                var builder = WebApplication.CreateBuilder(args);
                builder.Services.AddControllers();
                var app = builder.Build();
                app.MapControllers();
                app.Run();

                [ApiController, Route("orders")]
                public class OrdersController : ControllerBase
                {
                    [HttpPost]
                    public string Post(Order order) => "taken";
                }

                public class Order { [Required] public string? Name { get; set; } }
                """, ["200 OK", "204 No Content", "400 Bad Request", "500 Internal Server Error"], "400 Bad Request",
                "[ApiController] checks the model before the action runs, and answers 400 itself if it isn't valid."),
            Body("GET / then GET /", """
                var builder = WebApplication.CreateBuilder(args);
                builder.Services.AddOutputCache();
                var app = builder.Build();
                app.UseOutputCache();
                int hits = 0;
                app.MapGet("/", () => ++hits).CacheOutput();
                app.Run();
                """, ["1 1", "1 2", "0 1", "2 2"], "1 1",
                "CacheOutput keeps the response on the server. The second GET is answered from the cache, and the endpoint never runs."),
            Page("GET /", """
                @page
                @addTagHelper *, Microsoft.AspNetCore.Mvc.TagHelpers
                @functions {
                    public string? Name { get; set; } = "Ada";
                }
                <input asp-for="Name">
                """, ["<input type=\"text\" id=\"Name\" name=\"Name\" value=\"Ada\">", "<input asp-for=\"Name\">", "<input value=\"Ada\">", "<input name=\"Name\">"],
                "<input type=\"text\" id=\"Name\" name=\"Name\" value=\"Ada\">",
                "asp-for writes the rest from the property itself: its type, its name for the form, and its current value."),
            Body("GET /api/doors", """
                var app = WebApplication.Create(args);
                app.Map("/api", api => api.Run(ctx =>
                    ctx.Response.WriteAsync($"{ctx.Request.PathBase} {ctx.Request.Path}")));
                app.Run();
                """, ["/api /doors", " /api/doors", "/api/doors /doors", "/api /api/doors"], "/api /doors",
                "Inside app.Map's branch, the part it matched has moved from Path to PathBase, so a branch needn't know where it's mounted."),
            Ask("Which Blazor render mode runs a component's C# in the browser itself?",
                ["InteractiveWebAssembly", "InteractiveServer", "Static server rendering", "Prerendering"], "InteractiveWebAssembly",
                "InteractiveServer runs the C# on the server, sending changes over SignalR. WebAssembly downloads the .NET runtime and runs it in the browser."),
        ],
    };

    // One riddle for each dragon, a step harder than the level's own questions on the same topics.
    public static readonly Dictionary<(string Level, string Path), Question> Dragons = new()
    {
        [("easy", "cave")] = Body("GET /items", """
            var app = WebApplication.Create(args);
            app.MapGet("/items/{id?}", (int? id) => id is null ? "all" : $"item {id}");
            app.Run();
            """, ["all", "item ", "item 0", "404"], "all",
            "The ? makes that part of the route optional. With nothing there, the nullable id is simply null."),
        [("easy", "forest")] = Body("GET /hi", """
            var app = WebApplication.Create(args);
            app.MapGet("/hi/{name=stranger}", (string name) => $"Hi {name}");
            app.Run();
            """, ["Hi stranger", "Hi ", "Hi {name=stranger}", "(empty)"], "Hi stranger",
            "=stranger gives the route a default value, so it matches without that part of the path, and name gets the default."),
        [("easy", "castle")] = Page("GET /", """
            @page
            @{ string? who = null; }
            <p>[@who]</p>
            """, ["<p>[]</p>", "<p>[null]</p>", "<p>[@who]</p>", "500"], "<p>[]</p>",
            "Razor writes nothing at all for a null. It doesn't complain, and it doesn't print the word null."),
        [("medium", "cave")] = Body("GET /", """
            var builder = WebApplication.CreateBuilder(args);
            builder.Services.AddScoped<Bag>();
            var app = builder.Build();
            app.Use(async (ctx, next) =>
            {
                ctx.RequestServices.GetRequiredService<Bag>().Word = "same";
                await next();
            });
            app.MapGet("/", (Bag bag) => bag.Word);
            app.Run();

            class Bag { public string Word = "new"; }
            """, ["same", "new", "(empty)", "500"], "same",
            "One request is one scope, so the middleware and the endpoint are given the very same Bag."),
        [("medium", "forest")] = Status("GET /doors then GET /api/v1/doors", """
            var app = WebApplication.Create(args);
            var api = app.MapGroup("/api");
            var v1 = api.MapGroup("/v1");
            v1.MapGet("/doors", () => "Doors");
            app.Run();
            """, ["200 200", "200 404", "404 200", "404 404"], "404 200",
            "Each group adds its prefix, so the endpoint's whole route is /api/v1/doors, and nothing answers plain /doors."),
        [("medium", "castle")] = Page("GET /?door=gold", """
            @page
            @using Microsoft.AspNetCore.Mvc
            @functions {
                [BindProperty] public string? Door { get; set; }
            }
            <p>[@Door]</p>
            """, ["<p>[gold]</p>", "<p>[]</p>", "<p>[door=gold]</p>", "<p>[Door]</p>"], "<p>[]</p>",
            "[BindProperty] binds on POST only, unless you add SupportsGet = true, to keep a GET from overwriting a page's properties."),
        [("hard", "cave")] = Body("GET / then GET /", """
            var builder = WebApplication.CreateBuilder(args);
            builder.Services.AddScoped<Cart>();
            builder.Services.AddSingleton<Shop>();
            var app = builder.Build();
            app.MapGet("/", (Shop shop) => ++shop.Cart.Items);
            app.Run();

            class Cart { public int Items; }
            class Shop(Cart cart) { public Cart Cart { get; } = cart; }
            """, ["1 1", "1 2", "0 0", "500 500"], "1 2",
            "A captive dependency: the singleton is built once, and keeps the first scoped Cart for ever. Outside Development, nothing warns you."),
        [("hard", "forest")] = Body("GET / then GET /", """
            var app = WebApplication.Create(args);
            app.UseMiddleware<Hits>();
            app.MapGet("/", (HttpContext ctx) => ctx.Items["hits"]!.ToString());
            app.Run();

            class Hits(RequestDelegate next)
            {
                int count;
                public Task InvokeAsync(HttpContext ctx)
                {
                    ctx.Items["hits"] = ++count;
                    return next(ctx);
                }
            }
            """, ["1 1", "1 2", "0 1", "2 2"], "1 2",
            "A middleware class like this one is made once, when the pipeline is built, so its fields are shared by every request."),
        [("hard", "castle")] = Status("POST / name=Ada", """
            using Microsoft.AspNetCore.Mvc;

            var builder = WebApplication.CreateBuilder(args);
            builder.Services.AddAntiforgery();
            var app = builder.Build();
            app.UseAntiforgery();
            app.MapPost("/", ([FromForm] string name) => name);
            app.Run();
            """, ["200 OK", "400 Bad Request", "403 Forbidden", "415 Unsupported Media Type"], "400 Bad Request",
            "An endpoint reading a form expects an antiforgery token unless you call DisableAntiforgery(), and this request has none."),
    };

    // The final boss's nine questions: the darkest corners of ASP.NET.
    public static readonly Question[] Boss =
    [
        Status("GET /", """
            var builder = WebApplication.CreateBuilder(args);
            builder.Services.AddDistributedMemoryCache();
            builder.Services.AddSession();
            var app = builder.Build();
            app.MapGet("/", (HttpContext ctx) => ctx.Session.GetString("key") ?? "none");
            app.Run();
            """, ["200 OK", "400 Bad Request", "401 Unauthorized", "500 Internal Server Error"], "500 Internal Server Error",
            "AddSession only registers the services. WebApplication doesn't add UseSession for you, so ctx.Session throws: the lost session."),
        Both("GET /", """
            var app = WebApplication.Create(args);
            app.Run(async ctx =>
            {
                await ctx.Response.WriteAsync("Hi ");
                try
                {
                    ctx.Response.StatusCode = 404;
                }
                catch (InvalidOperationException)
                {
                    await ctx.Response.WriteAsync("too late");
                }
            });
            app.Run();
            """, ["200 Hi too late", "404 Hi ", "404 Hi too late", "500 Hi"], "200 Hi too late",
            "The first write sends the status and headers, and they can't be taken back. Setting the status after that throws."),
        Status("GET / then GET /", """
            using Microsoft.AspNetCore.RateLimiting;

            var builder = WebApplication.CreateBuilder(args);
            builder.Services.AddRateLimiter(o => o.AddFixedWindowLimiter("one", w =>
            {
                w.PermitLimit = 1;
                w.Window = TimeSpan.FromMinutes(1);
            }));
            var app = builder.Build();
            app.UseRateLimiter();
            app.MapGet("/", () => "ok").RequireRateLimiting("one");
            app.Run();
            """, ["200 200", "200 429", "200 503", "429 429"], "200 503",
            "Everyone expects 429, but the rate limiter's RejectionStatusCode starts at 503 until you set it yourself."),
        Log("GET /", """
            var app = WebApplication.Create(args);
            app.Use(async (ctx, next) =>
            {
                Console.Write(ctx.GetEndpoint() is null ? "none " : "found ");
                await next();
            });
            app.UseRouting();
            app.Use(async (ctx, next) =>
            {
                Console.Write(ctx.GetEndpoint() is null ? "none " : "found ");
                await next();
            });
            app.MapGet("/", () => "ok");
            app.Run();
            """, ["none none", "none found", "found found", "found none"], "none found",
            "UseRouting is where the endpoint is chosen, so anything before it can't see one. Leave it out, and WebApplication puts it first."),
        Body("GET /", """
            var builder = WebApplication.CreateBuilder(new WebApplicationOptions
            {
                Args = args,
                EnvironmentName = Environments.Development,
            });
            builder.Services.AddScoped<Cart>();
            builder.Services.AddSingleton<Shop>();
            var app = builder.Build();
            app.MapGet("/", (Shop shop) => ++shop.Cart.Items);
            app.Run();

            class Cart { public int Items; }
            class Shop(Cart cart) { public Cart Cart { get; } = cart; }
            """, ["1", "0", "(empty)", Crashes], Crashes,
            "In Development only, Build() validates the container. A singleton that depends on a scoped service is caught, and the app won't start.")
            with { Crash = "AggregateException" },
        Body("GET /", """
            using Microsoft.Extensions.DependencyInjection.Extensions;

            var builder = WebApplication.CreateBuilder(args);
            builder.Services.AddSingleton<IRune, Fire>();
            builder.Services.AddSingleton<IRune, Ice>();
            builder.Services.TryAddSingleton<IRune, Mud>();
            var app = builder.Build();
            app.MapGet("/", (IRune one, IEnumerable<IRune> all) =>
                $"{one.GetType().Name} {all.Count()}");
            app.Run();

            interface IRune { }
            class Fire : IRune { }
            class Ice : IRune { }
            class Mud : IRune { }
            """, ["Fire 2", "Ice 2", "Mud 3", "Ice 3"], "Ice 2",
            "Asking for one gets the last one registered, and asking for them all gets every one. TryAdd adds nothing if the type is already there."),
        Both("GET /", """
            var app = WebApplication.Create(args);
            app.UseExceptionHandler("/oops");
            app.MapGet("/", string () => throw new InvalidOperationException());
            app.MapGet("/oops", () => "Handled");
            app.Run();
            """, ["200 Handled", "500 Handled", "500 (empty)", "302 (empty)"], "500 Handled",
            "UseExceptionHandler runs the pipeline again for /oops, with no redirect, and keeps the status at 500 even though it was handled."),
        Page("GET /", """
            @page
            @{ string? css = null; bool off = false; }
            <p class="@css">A</p>
            <input disabled="@off">
            """, ["<p>A</p> <input>", "<p class=\"\">A</p> <input disabled=\"False\">", "<p class=\"\">A</p> <input disabled=\"\">", "<p class=\"null\">A</p> <input disabled=\"false\">"],
            "<p>A</p> <input>",
            "Razor's conditional attributes: when the whole value is null or false, it leaves out the whole attribute."),
        Status("GET /", """
            using System.Security.Claims;

            var builder = WebApplication.CreateBuilder(args);
            builder.Services.AddAuthentication().AddBearerToken();
            builder.Services.AddAuthorization();
            var app = builder.Build();
            app.Use(async (ctx, next) =>
            {
                var ada = new Claim(ClaimTypes.Name, "Ada");
                ctx.User = new(new ClaimsIdentity([ada], "Test"));
                await next();
            });
            app.MapGet("/", () => "Vault").RequireAuthorization();
            app.Run();
            """, ["200 OK", "401 Unauthorized", "403 Forbidden", "500 Internal Server Error"], "401 Unauthorized",
            "With the services registered and no UseAuthorization here, WebApplication adds it itself, before this middleware. By the time Ada is signed in, it has already said no."),
    ];
}
