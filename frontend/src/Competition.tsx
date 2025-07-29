import { useState } from 'react';

export const Competition = () => {
    const [ results, setResults ] = useState<RankedResult | null>();
    const [ value, setValue ] = useState("");
    const [ loading, setLoading ] = useState<boolean>(false);

    type RankedResult = {
        question: string;
        answers: Record<string, any>[];
        ranking: string[];
        rawRanking: string;
    }

    const runCompetition = async () => {
        const payload = {
            seed_prompt: value,
            competitors: [
                "gpt-4o-mini",
                "claude-3-7-sonnet-latest",
                "gemini-2.0-flash",
                "deepseek-chat",
                "llama-3.3-70b-versatile",
            ]
        }

        setLoading(true)

        try {
            const response = await fetch("/run", {
                method: "POST",
                headers: {"Content-Type": "application/json" },
                body: JSON.stringify(payload)
            })

            if (!response.ok) {
                throw new Error("Server error");
            }

            const data = await response.json()

            setResults(data);
        } catch (error) {
            console.log("Error running competition", error);
        }
        finally {
            setLoading(false)
        }
    };  

    const handleSubmit = () => {
        runCompetition();
    }

    if (loading) {
        return <p>Loading results... </p>
    }

    return (
        <div style={{display: "flex", flexDirection: "column", alignItems: "center"}}>
            <span style={{marginBottom: '3rem', fontSize: '3rem', fontFamily: 'sans-serif'}}>LLM Ranker</span>
            <span>Enter a question to ask multiple LLMs.</span>
            <span>We will prompt and ask each one, then rank the responses for you.</span>
            <form onSubmit={(e) => {
                e.preventDefault();
                handleSubmit();
            }} style={{display: "flex", flexDirection: "column", alignItems: "center"}}>
                <input style={{width: '40rem', height: '10rem', marginTop: '2rem'}} value={value} onChange={(e) => setValue(e.target.value)}></input>
                <button style={{marginTop: '2rem'}} type="submit">Submit</button>
            </form>

            {
                results && (
                    <div>
                        <h2 style={{marginTop: '4rem'}}>Question:</h2>
                        <p style={{marginBottom: '2rem'}}>{results.question}</p>

                        <h2>Answers:</h2>
                        {results.answers.map((answer, index) => (
                            <div key={index} style={{}}>
                                <h3>{answer.model}</h3>
                                <pre style={{     whiteSpace: "pre-wrap", fontFamily: "inherit", padding: "1rem", borderRadius: "8px", border: "1px solid #ddd", overflowX: "auto", maxWidth: "60rem", }}>
                                    {typeof answer.answer === "string" ? answer.answer : JSON.stringify(answer.answer, null, 2)}
                                </pre>
                            </div>
                        ))}

                        <h2>Ranking:</h2>
                        <ol>
                            {results.ranking.map((model, index) => (
                                <li key={index}>{model}</li>
                            ))}
                        </ol>
                    </div>
                )
            }
        </div>
    )
}