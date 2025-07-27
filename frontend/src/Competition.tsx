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
            const response = await fetch("http://localhost:8000/run", {
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
                        <h2>Question:</h2>
                        <p>{results.question}</p>

                        <h2>Answers:</h2>
                        {results.answers.map((answer, index) => (
                            <div key={index}>
                                <h4>{answer.model}</h4>
                                <p>{answer.answer}</p>
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