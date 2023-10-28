pub mod api;

pub fn CreateApi(platform: &str, amount: usize) -> std::io::Result<usize>{
    return api::CreateApi(platform, amount);
}