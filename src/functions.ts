import { AwsV4Signer } from 'aws4fetch'

export async function sign(url: string, access_key: string, secret_key: string) {
    const signer = new AwsV4Signer({
        url: url,
        accessKeyId: access_key,
        secretAccessKey: secret_key,
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
