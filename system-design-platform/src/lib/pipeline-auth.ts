export function checkPipelineAuth(request: Request) {
  const token = request.headers.get("authorization")?.replace("Bearer ", "");
  if (process.env.PIPELINE_TOKEN && token !== process.env.PIPELINE_TOKEN) {
    return false;
  }
  return true;
}
