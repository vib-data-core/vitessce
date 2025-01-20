import { AwsV4Signer } from 'aws4fetch'

export async function sign(url: string) {
    const signer = new AwsV4Signer({
        url: url,
        accessKeyId: import.meta.env.VITE_ACCESS_KEY,
        secretAccessKey: import.meta.env.VITE_SECRET_KEY,
        method: "GET",
        service: 's3'
    })
    const { method, headers, body } = await signer.sign()
    console.log(`Method: ` + method)
    console.log(`URL: ` + url)
    console.log(`Headers: ` + [...headers])
    console.log(`Body: ` + body)
    return headers
}
